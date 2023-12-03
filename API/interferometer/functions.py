import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
from astropy.coordinates import EarthLocation, AltAz, ITRS, CartesianRepresentation
from astropy.constants import c
import itertools
from io import BytesIO
import base64

pd.set_option('display.precision', 17)
np.set_printoptions(precision=20)

const_c = c.value   # speed of light [m/s]


def long2xyzbroad(coords):
    """
    Returns the nominal ITRF (X, Y, Z) coordinates [m] for a point at
    geodetic latitude and longitude [radians] and elevation [m].
    The ITRF frame used is not the official ITRF, just a right
    handed Cartesian system with X going through 0 latitude and 0 longitude,
    and Z going through the north pole.
    orig. source: http://www.oc.nps.edu/oc2902w/coord/llhxyz.htm
    """

    lat = np.radians(coords[:,0])
    lon = np.radians(coords[:,1])
    elevation = coords[:,2]


    er=6378137.0
    rf=298.257223563

    f=1./rf
    esq=2*f-f**2
    nu=er/np.sqrt(1.-esq*(np.sin(lat))**2)

    x=(nu+elevation)*np.cos(lat)*np.cos(lon)
    y=(nu+elevation)*np.cos(lat)*np.sin(lon)
    z=((1.-esq)*nu+elevation)*np.sin(lat)

    return np.column_stack((x,y,z))

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

def earth_location_to_local(location, reference_location):
    altaz = _earthlocation_to_altaz(location, reference_location)
    return altaz.cartesian.xyz

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

def h(hObs, gradDec, t_muestreo):

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
    plt.imshow(psf.real, cmap='gray', vmax=0.1)
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
    plt.imshow(sampling.real, cmap='plasma')
    #se lleva base64
    buf = BytesIO()
    figure.savefig(buf, format='png')
    image_sampling_base64 = base64.b64encode(buf.getvalue()).decode()
    
    return sampling, image_sampling_base64, image_psf_base64

def baselines(xyz):

    antenna_id = np.arange(0, len(xyz[:,0])) #cantidad de antenas
    antenna_pair_combinations = np.fromiter(itertools.chain(*itertools.combinations(antenna_id, 2)), dtype=int).reshape(-1,2) #combinaciones

    baselines = np.vstack([xyz[antenna_pair_combinations[:,0]] - xyz[antenna_pair_combinations[:,1]], 
                       xyz[antenna_pair_combinations[:,1]] - xyz[antenna_pair_combinations[:,0]]]) # se generan los baselines

    return baselines

def coverage(baseline, HA, dec, wavelength):
    R = calc_RR(HA, dec).transpose(2,0,1)
    coverage = np.dot(R, baseline.T)/wavelength #se divide por la longitud de onda
    #transpuesta para que no sean puntos (u,v) sobre un mapa sino que se vea como dado la rotación de la tierra se van generando elipses
    #caso contrario solo serían circulos
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
    return coverage, image_base64

def fft_model_image(path):
    img = cv2.imread(path,0)
    ffts = np.fft.fftshift(np.fft.fft2(img))
    pix = img.shape[0]
    return pix, ffts

def geodetic_to_local_xyz(df, reference_location):
    ant_pos = EarthLocation.from_geodetic(df[:,1], df[:,0], df[:,2])
    ref_loc = EarthLocation.from_geodetic(reference_location[1],reference_location[0],reference_location[2])
    x, y, z = earth_location_to_local(ant_pos, ref_loc)
    stack = np.column_stack((x.value,y.value,z.value))
    return stack

def simulation(t_obs, dec,t_muestreo, path, df, reference_location, frequency):
    wavelength = const_c / (frequency*1e9)
    coords = long2xyzbroad(df)
    #xyz = geodetic_to_local_xyz(df, reference_location)
    baseline = baselines(coords)
    HA, dec = h(t_obs, dec, t_muestreo)
    UV_coverage, img_coverage = coverage(baseline, HA, dec, wavelength)
    pixels, ffts=fft_model_image(path)
    sampling, img_sampling, img_psf = grid_sampling(pixels, np.max(np.abs(baseline)), UV_coverage, wavelength)
    obs= np.abs(np.fft.ifft2(np.fft.ifftshift(ffts*sampling)))
    boolean, buffer = cv2.imencode(".png", obs)
    stream = BytesIO(buffer)
    img_dirty_base64 = base64.b64encode(stream.getvalue()).decode()
    return img_dirty_base64, img_coverage, img_sampling, img_psf
