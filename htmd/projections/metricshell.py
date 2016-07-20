# (c) 2015-2016 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
from htmd.projections.metricdistance import MetricDistance
import numpy as np
import logging
logger = logging.getLogger(__name__)


class MetricShell(MetricDistance):
    """ Calculates the density of atoms around other atoms.

    The MetricShell class calculates the density of a set of
    interchangeable atoms in concentric spherical shells around some
    other atoms. Thus it can treat identical molecules (like water or
    ions) and calculate summary values like the changes in water density
    around atoms. It produces a n-by-s dimensional vector where n the
    number of atoms in the first selection and s the number of shells
    around each of the n atoms.

    Parameters
    ----------
    sims : numpy.ndarray of :class:`Sim <htmd.simlist.Sim>` objects or single :class:`Molecule <htmd.molecule.molecule.Molecule>` object
        A simulation list generated by the :func:`simlist <htmd.simlist.simlist>` function, or a :class:`Molecule <htmd.molecule.molecule.Molecule>` object
    sel1 : str
        Atomselection for the first set of atoms around which the shells will be calculated.
    sel2 : str
        Atomselection for the second set of atoms whose density will be calculated in shells around the first selection.
    numshells : int, optional
        Number of shells to use around atoms of sel1
    shellwidth : int, optional
        The width of each concentric shell in Angstroms
    pbc : bool, optional
        Set to false to disable distance calculations using periodic distances
    gap : int, optional
        Not functional yet
    truncate : float, optional
        Set all distances larger than `truncate` to `truncate`
    skip : int
        Skip every `skip` frames of the trajectories
    update :
        Not functional yet

    Returns
    -------
    data : :class:`MetricData <htmd.metricdata.MetricData>` object
        Returns a :class:`MetricData <htmd.metricdata.MetricData>` object containing the metrics calculated
    """
    def __init__(self, sel1, sel2, numshells=4, shellwidth=3, pbc=True, gap=None, truncate=None):
        super().__init__(sel1, sel2, None, None, 'distances', 8, pbc, truncate)

        self.numshells = numshells
        self.shellwidth = shellwidth
        self.map = None
        self.shellcenters = None

    def _precalculate(self, mol):
        self.map = super().getMapping(mol).indexes
        self.shellcenters = np.unique(self.map[:, 0])

    def project(self, *args, **kwargs):
        """ Project molecule.

        Parameters
        ----------
        mol : :class:`Molecule <htmd.molecule.molecule.Molecule>`
            A :class:`Molecule <htmd.molecule.molecule.Molecule>` object to project.
        kwargs :
            Do not use this argument. Only used for backward compatibility. Will be removed in later versions.

        Returns
        -------
        data : np.ndarray
            An array containing the projected data.
        """
        mol = args[0]
        (shellcenters, map, sel1, sel2) = self._getPrecalc(mol)
        distances = super().project(mol)
        return _shells(distances, map[:, 0], shellcenters, self.numshells, self.shellwidth)

    def _getSelections(self, mol):
        return super()._getSelections(mol)

    def _getPrecalc(self, mol):
        sel1, sel2 = self._getSelections(mol)
        if self.shellcenters is not None and self.map is not None:
            return self.shellcenters, self.map, sel1, sel2
        else:
            map = super().getMapping(mol).indexes
            return np.unique(map[:, 0]), map, sel1, sel2

    def getMapping(self, mol):
        idx, _ = super()._getSelections(mol)
        from pandas import DataFrame
        types = []
        indexes = []
        description = []
        for i in np.where(idx)[0]:
            for n in range(self.numshells):
                types += ['shell']
                indexes += [i]
                description += ['Density of sel2 atoms in shell {}-{} A centered on atom {} {} {}'
                                .format(n*self.shellwidth, (n+1)*self.shellwidth, mol.resname[i], mol.resid[i], mol.name[i])]
        return DataFrame({'type': types, 'indexes': indexes, 'description': description})


def _shells(distances, map, shellcenters, numshells, shellwidth):
    shelledges = np.arange(shellwidth*(numshells+1), step=shellwidth)
    shellvol = 4/3 * np.pi * (shelledges[1:] ** 3 - shelledges[:-1] ** 3)

    shellmetric = np.ones((np.size(distances, 0), len(shellcenters) * numshells)) * -1

    for i in range(len(shellcenters)):
        cols = map == shellcenters[i]
        for e in range(len(shelledges)-1):
            inshell = (distances[:, cols] > shelledges[e]) & (distances[:, cols] <= shelledges[e+1])
            shellmetric[:, (i*numshells)+e] = np.sum(inshell, axis=1) / shellvol[e]

    return shellmetric


if __name__ == "__main__":
    from htmd.molecule.molecule import Molecule
    from htmd.home import home
    from os import path
    mol = Molecule(path.join(home(), 'data', 'metricdistance', 'filtered.pdb'))
    mol.read(path.join(home(), 'data', 'metricdistance', 'traj.xtc'))
    metr = MetricShell('protein and name CA', 'resname MOL and noh')
    data = metr.project(mol)

    densities = np.array([0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
                          0.00095589,  0.        ,  0.        ,  0.        ,  0.00023897,
                          0.        ,  0.        ,  0.        ,  0.00191177,  0.        ,
                          0.        ,  0.        ,  0.        ,  0.        ,  0.        ])
    assert np.all(np.abs(data[193, 750:770] - densities) < 0.001), 'Shell density calculation is broken'