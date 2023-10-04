import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
from astropy.coordinates import EarthLocation, AltAz, ITRS, CartesianRepresentation
import itertools

const_c = 3e8   # speed of light [m/s]
frequency = 5e9              # observing frequency [Hz]
wavelength = const_c/frequency # receiving wavelength [metres]

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

def h(hObs, gradDec):

    """ 
    Cambia la duración de la observación a X horas
    Muestreo cada 0.1 hrs - 6 min
       """

    observacion_grados = hObs * 15.0
    HA = np.arange(-np.radians(observacion_grados), np.radians(observacion_grados), np.radians(0.1))  # [radianes]
    dec = np.radians(gradDec)
    return HA, dec

def grid_sampling(piximg, max_B, coverage):
    """ 
    piximg: cantidad de pixeles de la imagen modelo, tiene que ser nxn
    max_B: baseline mas largo
    uvcoverage: array uv cobertura

       """
    sampling = np.zeros((piximg, piximg)) + 1j*np.zeros((piximg, piximg))
    min_lambda=wavelength #minima longitud de onda lambda
    delta_x = (min_lambda / max_B) / 7
    delta_u = 1 / ((piximg * delta_x) + 0.00001)

    u_pixel2 = np.floor(0.5 + coverage[:, 0] / delta_u + piximg / 2).astype(int)
    v_pixel2 = np.floor(0.5 + coverage[:, 1] / delta_u + piximg / 2).astype(int)
      
    # S(u,v) = 1 otro caso S=0
    sampling[v_pixel2, u_pixel2] = 1.0

    return sampling

def baselines(xyz):

    antenna_id = np.arange(0, len(xyz[:,0])) #cantidad de antenas
    antenna_pair_combinations = np.fromiter(itertools.chain(*itertools.combinations(antenna_id, 2)), dtype=int).reshape(-1,2) #combinaciones

    baselines = np.vstack([xyz[antenna_pair_combinations[:,0]] - xyz[antenna_pair_combinations[:,1]], 
                       xyz[antenna_pair_combinations[:,1]] - xyz[antenna_pair_combinations[:,0]]]) # se generan los baselines

    return baselines

def coverage(baseline, HA, dec):
    R = calc_RR(HA, dec).transpose(2,0,1)
    coverage = np.dot(R, baseline.T)/wavelength #se divide por la longitud de onda
    #transpuesta para que no sean puntos (u,v) sobre un mapa sino que se vea como dado la rotación de la tierra se van generando elipses
    #caso contrario solo serían circulos
    return coverage

def fft_model_image(path):
    img = cv2.imread(path,0)
    ffts = np.fft.fftshift(np.fft.fft2(img))
    pix = img.shape[0]
    return pix, ffts

def geodetic_to_local_xyz(df, reference_location):
    ant_pos = EarthLocation.from_geodetic(df['latitude'], df['longitude'], df['altitude'])
    ref_loc = EarthLocation.from_geodetic(reference_location[0],reference_location[1],reference_location[2])
    x, y, z = earth_location_to_local(ant_pos, ref_loc)
    stack = np.column_stack((x.value,y.value,z.value))
    return stack

def simulation(t_obs, dec, path, df, reference_location):
    print(df)
    print("----------")
    print(reference_location)
    xyz = geodetic_to_local_xyz(df, reference_location)
    baseline = baselines(xyz)
    HA, dec = h(t_obs, dec)
    UV_coverage = coverage(baseline, HA, dec)
    pixels, ffts=fft_model_image('./interferometer/media/cat1.jpg')
    sampling = grid_sampling(pixels, np.max(np.abs(baseline)), UV_coverage)
    obs= np.abs(np.fft.ifft2(np.fft.ifftshift(ffts*sampling)))
    cv2.imwrite('interferometer/media/obs.png', obs)
