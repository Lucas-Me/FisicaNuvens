# Script responsavel pelos plots de concentracao, raio efetivo e conteudo de agua na nuvem

#---IMPORTS----------------------------------------------------------------------------------------
import os

import matplotlib as mpl
import matplotlib.pyplot as plt  # the plotting interface
import matplotlib.colors as mcolors
import numpy as np  # for numerical array computations
import matplotlib.tri as tri

#---IMPORTS LOCAIS----------------------------------------------------------------------------------------

from cloudsat_functions import get_hdf_geodata, get_hdf_data
import cloudsat_utils

#---VARIAVEIS E PREPARATIVOS--------------------------------------------------------------------------
# Diretorios de entrada e saida de arquivos
input_ = '/mnt/f/lucas/conteudo/fisica das nuvens e precipitacao/Dados'
output = '/mnt/f/lucas/conteudo/fisica das nuvens e precipitacao/Figuras'

# nome do arquivo _
# cwc_fname = '2019055170406_68325_CS_2B-CWC-RO_GRANULE_P1_R05_E08_F03.h5'
# ecmwf_fname = '2019055170406_68325_CS_ECMWF-AUX_GRANULE_P_R05_E08_F03.h5'

# nome do arquivo CWC-RO e do AUX-ECMWF
cwc_fname = '2006235200711_01711_CS_2B-CWC-RO_GRANULE_P1_R05_E02_F00.hdf'
ecmwf_fname = '2006235200711_01711_CS_ECMWF-AUX_GRANULE_P_R05_E02_F00.hdf'

# recorte da area de estudo
lat_min = 17.1
lat_max = 28.6
lon_min = -114.8
lon_max = -112
extent = [lon_min, lon_max, lat_min, lat_max] # South America


#--------------------------------------------Cloudsat Temperatura --------------------------------------------------------------------------

# Temperatura retirado do ECMWF e interpolado na trajetoria do cloudsat
ecmwf_temp = get_hdf_data(os.path.join(input_, ecmwf_fname), 'Temperature')

# demais dimensoes do dado do ecmwf interpolado no cloudsat
ecmwf_lons, ecmwf_lats, ecmwf_height, ecmwf_time, ecmwf_elev = get_hdf_geodata(
    os.path.join(input_, ecmwf_fname),
    varnames = ["Longitude", "Latitude", "EC_height", "Profile_time", "DEM_elevation"]
)

# Encontrar indices do array onde o recorte da area esta localizado
# diferente pro dado interpolado e pro extraido diretamente do cloudat (secao anterior)
ii = np.where(
    (ecmwf_lons > lon_min)
    & (ecmwf_lons < lon_max)
    & (ecmwf_lats > lat_min)
    & (ecmwf_lats < lat_max)
)[0]
i1, i2 = ii[0], ii[-1]

# grade na horizontal
ecmwf_x = np.arange(i1, i2, dtype = np.float32)

# grade na vertical
ecmwf_z0 = 0  # km
ecmwf_z1 = 16  # km
ecmwf_nz = 1000  # Number of pixels (levels) in the vertical.
ecmwf_z = (ecmwf_height * 1e-3).astype(np.float32)

# indexando a variavel temperatura potencial
temperature = ecmwf_temp [i1:i2, :]

# interpolar a temperatura potencial para os niveis de referencia
temperature = cloudsat_utils._interp2d_ecmwf(
    temperature,
    ecmwf_x,
    ecmwf_z,
    i1,
    i2,
    i2 - i1,
    ecmwf_z1,
    ecmwf_z0,
    ecmwf_nz,
).T[::-1, :]

#--------------------------------------------Cloudsat Conteudo de agua liquda--------------------------------------------------------------------------

# variaveis da goticula, retirada do cloudsat
radius = get_hdf_data(os.path.join(input_, cwc_fname),'RO_ice_effective_radius') # micrometro
concentracao = get_hdf_data(os.path.join(input_, cwc_fname), 'RO_ice_number_conc') # cm^{-3}
conteudo = get_hdf_data(os.path.join(input_, cwc_fname), 'RO_ice_water_content') # mg/m^3

# demais dimensoes do dado do ecmwf interpolado no cloudsat
cwc_lons, cwc_lats, cwc_height, cwc_time, cwc_elev = get_hdf_geodata(
    os.path.join(input_, cwc_fname), 
    varnames = ["Longitude", "Latitude", "Height", "Profile_time", "DEM_elevation"]
)

# Encontrar indices do array onde o recorte da area esta localizado
# diferente pro dado interpolado e pro extraido diretamente do cloudat (secao anterior)
jj = np.where(
    (cwc_lons > lon_min)
    & (cwc_lons < lon_max)
    & (cwc_lats > lat_min)
    & (cwc_lats < lat_max)
)[0]
j1, j2 = jj[0], jj[-1]

# grade na horizontal
cwc_x = np.arange(j1, j2, dtype = np.int64)
nx = j2 - j1

# grade na vertical
cwc_z0 = 0  # km
cwc_z1 = 16  # km
cwc_nz = 125  # Number of pixels (levels) in the vertical.
cwc_z = (cwc_height * 1e-3).astype(np.float32)[j1:j2, :]
zi = np.linspace(cwc_z0, cwc_z1, cwc_nz)

# coordenadas e valores
XX = np.tile(cwc_x, (125, 1)).T
x_coords = np.ravel(XX)
y_coords = np.ravel(cwc_z)
coords = np.column_stack((x_coords, y_coords))

# interpolar a temperatura potencial para os niveis de referencia
triang = tri.Triangulation(coords[:, 0], coords[:, 1])
Xi, Yi = np.meshgrid(cwc_x, zi)

# indexando as variaveis
radius = radius[j1:j2, :]
concentracao = concentracao[j1:j2, :]
conteudo = conteudo[j1:j2, :]*1e-3

vars_ = [radius, concentracao, conteudo]
for i in range(len(vars_)):
    interpolator = tri.LinearTriInterpolator(
        triang,
        np.ravel(vars_[i])
    )
    vars_[i] = interpolator(Xi, Yi)

#---Plotando os dados--------------------------------------------------------------------------

# Criando a figura e algumas constantes
fig, ax = plt.subplots(figsize=(22, 22), dpi = 200, nrows = 3, ncols = 1)
labels = [
    'Raio efetivo do gelo (um) e Temperatura (??C)',
    'Concentra????o de part??culas de gelo (1/L) e Temperatura (??C)',
    'Conte??do de gelo (g/m??) e Temperatura (??C)'
]

# intervalos de contorno das variaveis
clevs = [
    np.linspace(0, 180, 10), # radius, micrometros
    np.linspace(0, 400, 10), # concentracao, 1/L
    np.linspace(0, 2, 10) # conteudo, g/m^3
]

# lista de cores, em ordem crescete. RGBA
colors = np.array([
    'blue',
    'dodgerblue',
    'cyan',
    'palegreen',
    'gold', 
    'darkorange',
    'red'
])

# eixo horizontal
xticks, xticklabels = cloudsat_utils.xticks_alongtrack(
    x_indices = cwc_x,
    x_lons = cwc_lons[j1:j2],
    x_lats = cwc_lats[j1:j2],
    bins = 6
)

for row in range(3):
    # plot das isolinhas de temperatura
    kw_clabels = {'fontsize': 12, 'inline': True, 'inline_spacing': 5, 'fmt': '%i',
                'rightside_up': True, 'use_clabeltext': True}
    temp_contour = ax[row].contour(
        # ecmwf_lats[i1:i2],
        ecmwf_x,
        np.linspace(ecmwf_z0, ecmwf_z1, ecmwf_nz),
        temperature - 273.15,
        np.linspace(-60, 20, 5),
        colors='green',
        linewidths=1.25,
        linestyles='dashed'
    )
    ax[row].clabel(temp_contour, **kw_clabels) 

    # cria um novo cmap a partir do pre-existente
    var_cmap = mcolors.LinearSegmentedColormap.from_list(
        'Custom cmap', colors, clevs[row].shape[0] - 1)
    var_cmap.set_bad('w')
    var_cmap.set_under('darkblue')
    var_cmap.set_over('darkred')

    # nromaliza com base nos intervalos
    var_norm = mpl.colors.BoundaryNorm(clevs[row], var_cmap.N, clip = False)
    var_kw = dict(cmap=var_cmap, norm=var_norm)

    # plot contourf
    p = ax[row].contourf(
        #np.take(cwc_lats, Xi),
        Xi,
        Yi,
        vars_[row],
        levels = clevs[row],
        extend = 'max',
        **var_kw
    )
    cbar = fig.colorbar(p, location = 'right', pad = 0.02, ax = ax[row], extend = 'max')

    # titulos e eixos
    ax[row].set_xlabel("Latitude (??)")
    ax[row].set_ylabel("Altitude (Km)")
    ax[row].set_title(labels[row], loc='left')
    #ax[row].set_xticks(xticks)
    #ax[row].set_xticklabels(xticklabels)

    # plot da elevacao
    ax[row].fill_between(
        #cwc_lats[j1:j2],
        cwc_x,
        cwc_elev[j1:j2]*1e-3,
        color = "black"
    )

    # limite vertical do plot
    ax[row].set_ylim(bottom = 0)

# salvando a figura
plt.savefig(os.path.join(output, 'propriedades_gelo.png'), bbox_inches='tight')
plt.close()
