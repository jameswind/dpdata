#!/usr/bin/env python3

import numpy as np
import sys

ry2ev = 13.605693009
bohr2ang = 0.52917721067
kbar2evperang3 = 1./1602

def get_block (lines, keyword, skip = 0) :
    ret = []
    for idx,ii in enumerate(lines) :
        if keyword in ii :
            blk_idx = idx + 1 + skip
            while len(lines[blk_idx]) == 0:
                blk_idx += 1
            while len(lines[blk_idx]) != 0 and blk_idx != len(lines):
                ret.append(lines[blk_idx])
                blk_idx += 1
            break
    return ret

def get_cell (lines) :
    ret = []
    for idx,ii in enumerate(lines):
        if 'ibrav' in ii :
            break
    blk = lines[idx:idx+2]
    ibrav = int(blk[0].replace(',','').split('=')[-1])
    if ibrav == 0:
        blk = get_block(lines, 'CELL_PARAMETERS')
        for ii in blk:
            ret.append([float(jj) for jj in ii.split()[0:3]])
        ret = np.array(ret)
    elif ibrav == 1:
        a = float(blk[1].split('=')[-1])
        ret = np.array([[a,0.,0.],[0.,a,0.],[0.,0.,a]])
    else:
        sys.exit('ibrav > 1 not supported yet.')
    return ret

def get_coords (lines) :
    coord = []
    atom_symbol_list = []
    blk = get_block(lines, 'ATOMIC_POSITIONS')
    for ii in blk:
        coord.append([float(jj) for jj in ii.split()[1:4]])
        atom_symbol_list.append(ii.split()[0])
    coord = np.array(coord)
    atom_symbol_list = np.array(atom_symbol_list)
    tmp_names, symbol_idx = np.unique(atom_symbol_list, return_index=True)
    atom_types = []
    atom_numbs = []
    #preserve the atom_name order
    atom_names = atom_symbol_list[np.sort(symbol_idx)]
    for jj in atom_symbol_list:
        for idx, ii in enumerate(atom_names):
            if (jj == ii) :
                atom_types.append(idx)
    for idx in range(len(atom_names)):
        atom_numbs.append(atom_types.count(idx))
    atom_types = np.array(atom_types)

    return list(atom_names), atom_numbs, atom_types, coord

def get_energy (lines) :
    for ii in lines :
        if '!    total energy' in ii :
            return ry2ev * float(ii.split('=')[1].split()[0])
    return None

def get_force (lines) :
    blk = get_block(lines, 'Forces acting on atoms', skip = 1)
    ret = []
    for ii in blk:
        ret.append([float(jj) for jj in ii.split('=')[1].split()])
    ret = np.array(ret)
    ret *= (ry2ev / bohr2ang)
    return ret

def get_stress (lines) :
    blk = get_block(lines, 'total   stress')
    ret = []
    for ii in blk:
        ret.append([float(jj) for jj in ii.split()[3:6]])
    ret = np.array(ret)
    ret *= kbar2evperang3
    return ret
   
def get_frame (fout):
    outlines = open(fout, 'r').read().split('\n')
    # the name of the input file is assumed to be different from the output by 'in' and 'out' 
    inlines = open(fout.replace('out','in'), 'r').read().split('\n')
    atom_names, natoms, types, coords      = get_coords(inlines)
    cell        = get_cell  (inlines)
    energy      = get_energy(outlines)
    force       = get_force (outlines)
    stress      = get_stress(outlines) * np.linalg.det(cell)
    return atom_names, natoms, types, cell[np.newaxis, :, :], coords[np.newaxis, :, :], \
           np.array(energy)[np.newaxis], force[np.newaxis, :, :], stress[np.newaxis, :, :]
