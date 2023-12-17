import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
from astropy.coordinates import EarthLocation, AltAz, ITRS
from astropy.constants import c
from io import BytesIO
import base64
import cmcrameri.cm as cmc

const_c = c.value   # speed of light [m/s]


def new_positions(df, reference, scale):

    lats = df[:,0]
    lons = df[:,1]
    
    # Bearing
    dLons = np.radians(lons - reference[1])
    y = np.sin(dLons) * np.cos(np.radians(lats))
    x = np.cos(np.radians(reference[0])) * np.sin(np.radians(lats)) - np.sin(np.radians(reference[0])) * np.cos(np.radians(lats)) * np.cos(dLons)
    bearing = np.degrees(np.arctan2(y, x))
    bearing = np.trunc((bearing + 360) % 360)

    # Nuevas posiciones
    R = 6371000
    latRef = np.radians(reference[0])
    lonRef = np.radians(reference[1])
    bearing = np.radians(bearing)

    delta_lats = np.radians(lats) - latRef
    delta_lons = np.radians(lons) - lonRef

    a = np.sin(delta_lats / 2.0)**2 + np.cos(latRef) * np.cos(np.radians(lats)) * np.sin(delta_lons / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    # Calcular la distancia para cada par de puntos
    distances = (R * c) * scale 

    lat2 = np.arcsin(np.sin(latRef) * np.cos(distances / R) + np.cos(latRef) * np.sin(distances / R) * np.cos(bearing))
    lon2 = lonRef + np.arctan2(np.sin(bearing) * np.sin(distances / R) * np.cos(latRef), np.cos(distances / R) - np.sin(latRef) * np.sin(lat2))
    

    arr = np.column_stack((np.degrees(lat2), np.degrees(lon2), df[:,2]))


    return arr

def _earthlocation_to_altaz(location, reference_location):
    itrs_cart = location.get_itrs().cartesian
    itrs_ref_cart = reference_location.get_itrs().cartesian
    local_itrs = ITRS(itrs_cart - itrs_ref_cart, location=reference_location)
    return local_itrs.transform_to(AltAz(location=reference_location))

def earth_location_to_local_enu(location, reference_location):
    altaz = _earthlocation_to_altaz(location, reference_location)
    ned_coords =  altaz.cartesian.xyz
    enu_coords = ned_coords[1], ned_coords[0], -ned_coords[2]
    return np.array(enu_coords)

def enu_to_local_altaz(enu_baselines, distance):
    elevation = np.arctan2(enu_baselines[0], enu_baselines[1])
    azimuth = np.arcsin(enu_baselines[2]/distance)
    return elevation, azimuth

def calc_RR(H,dec):
    """
    Dado la rotación de la tierra, el objeto se "desplaza" en el cielo, por lo tanto se utiliza el
    ángulo horario y declinación para seguir su posición en el cielo.
    """
    if np.isscalar(H):
        H = np.array([H])

    R = np.array([[np.sin(H), np.cos(H), np.zeros_like(H)],\
        [-np.sin(dec)*np.cos(H), np.sin(dec)*np.sin(H), np.cos(dec*np.ones_like(H))],\
        [np.cos(dec)*np.cos(H), -np.cos(dec)*np.sin(H), np.sin(dec*np.ones_like(H))]])

    return R

def compute_h(hObs, gradDec, t_muestreo):

    """ 
    hObs: tiempo de observación en horas
    gradDec: declinación en grados
    t_muestreo: tiempo de muestreo en minutos
       """

    observacion_grados = hObs * 15.0
    HA = np.arange(-np.radians(observacion_grados), np.radians(observacion_grados), np.radians(t_muestreo/60))  # [radianes]
    dec = np.radians(gradDec)
    return HA, dec

def grid_sampling(piximg, max_B, coverage, wavelength):
    """ 
    piximg: cantidad de pixeles de la imagen modelo, tiene que ser nxn
    max_B: baseline mas largo
    uvcoverage: array uv cobertura
    wavelength: longitud de onda

       """
    sampling = np.zeros((piximg, piximg)) + 1j*np.zeros((piximg, piximg))
    uvgrid = np.zeros((piximg, piximg)) + 1j*np.zeros((piximg, piximg))
    min_lambda=wavelength #minima longitud de onda lambda
    delta_x = (min_lambda / max_B) / 7
    delta_u = 1 / ((piximg * delta_x) + 0.0000001)

    u_pixel2 = np.floor(0.5 + coverage[:, 0] / delta_u + piximg / 2).astype(int)
    v_pixel2 = np.floor(0.5 + coverage[:, 1] / delta_u + piximg / 2).astype(int)
    
    #psf
    np.add.at(uvgrid, (v_pixel2, u_pixel2), 1.0 + 1j*0.0)
    psf = np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(uvgrid)))
    fft_norm = np.max(psf.real)
    psf/= fft_norm
    #se grafica
    figurePSF = plt.figure(figsize=(8, 8))
    plt.subplot()
    plt.title('Point Spread Function')
    plt.imshow(psf.real, cmap=cmc.navia_r, vmax=0.1)
    #se lleva a base64
    bufPSF = BytesIO()
    figurePSF.savefig(bufPSF, format='png')
    image_psf_base64 = base64.b64encode(bufPSF.getvalue()).decode()

    # S(u,v) = 1 otro caso S=0
    sampling[v_pixel2, u_pixel2] = 1.0
    #se grafica
    figure = plt.figure(figsize=(8, 8))
    plt.subplot()
    plt.title('Cobertura cuadriculada')
    plt.imshow(sampling.real, cmap=cmc.navia_r)
    #se lleva base64
    buf = BytesIO()
    figure.savefig(buf, format='png')
    image_sampling_base64 = base64.b64encode(buf.getvalue()).decode()
    
    return sampling, image_sampling_base64, image_psf_base64

def baselines(enu_coords):
    """
    enu_coords: arreglo de coordenadas en el sistema de referencia plano tangente local (ENU)
    """
    b_enu = enu_coords[..., np.newaxis] - enu_coords[:, np.newaxis,:]
    b_enu = b_enu[:, ~np.eye(b_enu.shape[-1],dtype=bool)]
    return b_enu

def bENU_to_bEquatorial(b_enu, lat_obs):
    """
    b_enu: coordenadas de los baselines en el sistema de referencia plano tangente local (ENU)
    lat_obs: latitud del centro del observatorio, expresado en grados
    """
    latitude = np.radians(lat_obs)
    abs_b = np.sqrt(np.sum(b_enu**2, axis=0))  + 0.0000000000001

    azimuth, elevation = enu_to_local_altaz(b_enu, abs_b)

    x_equatorial = np.cos(latitude) * np.sin(elevation) - np.sin(latitude) * np.cos(elevation) * np.cos(azimuth)
    y_equatorial = np.cos(elevation) * np.sin(azimuth)
    z_equatorial = np.sin(latitude) * np.sin(elevation) + np.cos(latitude) * np.cos(elevation) * np.cos(azimuth)

    baseline_equatorial = abs_b * np.vstack([x_equatorial, y_equatorial, z_equatorial])
    
    return baseline_equatorial

""" def coverage(baseline, HA, dec, wavelength):
    R = calc_RR(HA, dec).transpose(2,0,1)
    coverage = np.dot(R, baseline.T)/wavelength #se divide por la longitud de onda

    #se grafica

    fig = plt.figure(figsize=(8,8))
    plt.title("Cobertura UV")
    plt.scatter(x=coverage[:,0],y=coverage[:,1], c="black", marker='.')
    plt.xlabel(r'$u\ \lambda$')  # Usa 'r' antes de la cadena de texto para que Python la trate como raw string
    plt.ylabel(r'$v\ \lambda$')
    #se lleva a base64
    buf = BytesIO()
    fig.savefig(buf, format='png')
    image_base64 = base64.b64encode(buf.getvalue()).decode()
    return coverage, image_base64 """

def coverage(baselines, HA, dec, wavelength):
    """
    baselines: arreglo de coordenadas de los baselines en el sistema ecuatorial
    HA: Ángulo horario en horas
    dec: declinación en radianes,
    wavelength: longitud de onda
    """
    R_matrix = calc_RR(HA, dec)
    uvw_meters = np.sum(R_matrix[...,np.newaxis]*baselines[np.newaxis,:,np.newaxis,:], axis=1)
    UV_coverage = np.column_stack((uvw_meters[0].reshape(-1), uvw_meters[1].reshape(-1)))/wavelength

    #se grafica
    fig = plt.figure(figsize=(8,8))
    plt.title("Cobertura UV")
    plt.scatter(x=UV_coverage[:,0],y=UV_coverage[:,1], c="black", marker='.', s=0.4)
    plt.xlabel(r'$u\ [k\lambda]$')  # Usa 'r' antes de la cadena de texto para que Python la trate como raw string
    plt.ylabel(r'$v\ [k\lambda]$')
    #se lleva a base64
    buf = BytesIO()
    fig.savefig(buf, format='png')
    image_base64 = base64.b64encode(buf.getvalue()).decode()

    return UV_coverage, image_base64

def fft_model_image(path):
    img = cv2.imread(path,0)
    ffts = np.fft.fftshift(np.fft.fft2(img))
    pix = img.shape[0]
    return pix, ffts

def geodetic_to_enu(df, reference_location):
    ant_pos = EarthLocation.from_geodetic(df[:,1], df[:,0], df[:,2])
    ref_loc = EarthLocation.from_geodetic(reference_location[1],reference_location[0],reference_location[2])
    enu_coords = earth_location_to_local_enu(ant_pos, ref_loc)
    return enu_coords

def simulation(t_obs, dec,t_muestreo, path, df, reference_location, frequency):
    wavelength = const_c / (frequency*1e9)
    enu_coords = geodetic_to_enu(df, reference_location)
    baseline = baselines(enu_coords)
    baseline_equatorial = bENU_to_bEquatorial(baseline, reference_location[0])
    HA, dec = compute_h(t_obs, dec, t_muestreo)
    UV_coverage, img_coverage = coverage(baseline_equatorial, HA, dec,wavelength)
    pixels, ffts=fft_model_image(path)
    sampling, img_sampling, img_psf = grid_sampling(pixels, np.max(np.abs(baseline_equatorial)), UV_coverage, wavelength)
    obs= np.abs(np.fft.ifft2(np.fft.ifftshift(ffts*sampling)))
    boolean, buffer = cv2.imencode(".png", obs)
    stream = BytesIO(buffer)
    img_dirty_base64 = base64.b64encode(stream.getvalue()).decode()
    return img_dirty_base64, img_coverage, img_sampling, img_psf
