#!/usr/bin/env python
"""k1c_stamp.py -- add the keys the compiler's dump loader expects to dumps
that lack them (schema tag, orbital energies, provenance), in place.

    python k1c_stamp.py k1_corpus            # every .npz in the directory
    python k1c_stamp.py k1_corpus/lih_r1p596.npz

A dump that already carries every key is left untouched. Arrays are never
altered; the file is rewritten atomically.
"""
import glob
import os
import sys
import time

import numpy as np

DUMP_SCHEMA = "tucc-psi4-dump-1"


def orbital_energies(h, eri, na, nb):
    n = h.shape[0]
    eps = np.zeros(n)
    for p in range(n):
        v = h[p, p]
        for j in range(na):
            v += eri[p, p, j, j] - 0.5 * eri[p, j, j, p]
        for j in range(nb):
            v += eri[p, p, j, j] - 0.5 * eri[p, j, j, p]
        eps[p] = v
    return eps


def stamp(path):
    z = np.load(path, allow_pickle=True)
    d = {k: z[k] for k in z.files}
    add = {}
    if "schema" not in d:
        add["schema"] = DUMP_SCHEMA
    if "mo_energy" not in d:
        add["mo_energy"] = orbital_energies(np.asarray(d["h_mo"], float),
                                            np.asarray(d["eri_mo"], float),
                                            int(d["n_alpha"]), int(d["n_beta"]))
    if "nmo" not in d:
        add["nmo"] = int(np.asarray(d["h_mo"]).shape[0])
    if "n_elec" not in d:
        add["n_elec"] = int(d["n_alpha"]) + int(d["n_beta"])
    if "program" not in d:
        add["program"] = "pyscf"
    if "created" not in d:
        add["created"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if not add:
        return []
    d.update(add)
    tmp = path + ".tmp.npz"
    np.savez(tmp, **d)
    os.replace(tmp, path)
    return sorted(add)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    paths = []
    for a in sys.argv[1:]:
        paths += sorted(glob.glob(os.path.join(a, "*.npz"))) if os.path.isdir(a) else [a]
    n = 0
    for p in paths:
        added = stamp(p)
        if added:
            n += 1
            print("%s: added %s" % (os.path.basename(p), ", ".join(added)))
    print("%d of %d dump(s) updated" % (n, len(paths)))


if __name__ == "__main__":
    main()
