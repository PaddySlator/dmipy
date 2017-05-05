from numpy.testing import assert_almost_equal, assert_equal
from microstruktur.signal_models import three_dimensional_models, utils
from microstruktur.signal_models.spherical_convolution import (kernel_sh_to_rh,
                                                               sh_convolution)
from dipy.reconst.shm import sf_to_sh, sh_to_sf
from dipy.data import get_sphere
import numpy as np
DIFFUSIVITY_SCALING = 1e-3


def test_spherical_convolution_watson_sh(sh_order=4):
    sphere = get_sphere('symmetric724')
    indices_sphere_orientations = np.arange(sphere.vertices.shape[0])
    np.random.shuffle(indices_sphere_orientations)
    mu_index = indices_sphere_orientations[0]
    mu_watson = sphere.vertices[mu_index]
    mu_watson_sphere = utils.cart2sphere(mu_watson)[1:]
    
    watson = three_dimensional_models.SD3Watson(mu=mu_watson_sphere, kappa=10.)
    f_sf = watson(n=sphere.vertices)
    f_sh = sf_to_sh(f_sf, sphere, sh_order)
    
    bval = 1e3
    lambda_par = 2e-3 * DIFFUSIVITY_SCALING
    stick = three_dimensional_models.I1Stick(mu=[0, 0], lambda_par=lambda_par)
    k_sf = stick(bvals=bval, n=sphere.vertices)
    k_sh = sf_to_sh(k_sf, sphere, sh_order)
    k_rh = kernel_sh_to_rh(k_sh, sh_order)
    
    fk_convolved_sh = sh_convolution(f_sh, k_rh, sh_order)
    fk_convolved_sf = sh_to_sf(fk_convolved_sh, sphere, sh_order)
    
    # assert if spherical mean is the same between kernel and convolved kernel
    assert_almost_equal(np.mean(k_sf), np.mean(fk_convolved_sf), 2)
    # assert if the lowest signal attenuation (E(b,n)) is orientation along
    # the orientation of the watson distribution.
    min_position = np.argmin(fk_convolved_sf)
    
    if min_position == mu_index:
        assert_equal(min_position, mu_index)
    else:  # then it's the opposite direction
        sphere_positions = np.arange(sphere.vertices.shape[0])
        opposite_index = np.all(
            np.round(sphere.vertices - mu_watson, 2) == 0, axis=1
        )
        min_position_opposite = sphere_positions[opposite_index]
        assert_equal(min_position_opposite, mu_index)
