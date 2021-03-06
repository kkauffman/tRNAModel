import numpy as np
from abc import ABCMeta, abstractmethod

from site_types import Ring_Site_Types
from aars_space import AARS_Space
from trna_space import TRNA_Space, Id_TRNA_Space
from code import Code

def hamming_dist(from_, to, length):
    dist = 0
    for i in xrange(length):
        if from_ & (2**i) != to & (2**i):
            dist += 1

    return dist

def get_hamming_distance_mutation_matrix(length, mu):
    mut_matrix = np.zeros((2**length, 2**length))
    
    for i in xrange(2**length):
        for j in xrange(2**length):
            diff = hamming_dist(i, j, length)
            mut_matrix[i,j] = mu**diff * (1 - mu)**(length - diff)

    return mut_matrix

def get_ring_mutation_matrix(size, mu):
    mut_matrix = np.diag([1.0 - (2 * mu)] * size)

    for i in xrange(size):
        mut_matrix[i][i - 1] = mu
        mut_matrix[i][i + 1 if (i + 1) < size else 0 ] = mu # Handles wraping around to 0

    return mut_matrix

def get_uniform_mutation_matrix(size, mu):
    mut_matrix = np.diag([1 - ((size-1) * mu)] * size)

    for i in xrange(size):
        for j in xrange(size):
            if i != j:
                mut_matrix[i][j] = mu

    return mut_matrix

class _Model(object):
    __metaclass__ = ABCMeta

    def __init__(self, args, rng):
        pass

    @abstractmethod
    def get_site_types(self):
        pass

    @abstractmethod
    def get_message_mutation_matrix(self):
        pass

    @abstractmethod
    def get_initial_code(self):
        pass

class Ring_Bit_Model(_Model):
    def __init__(self, args, rng):
        super(Ring_Bit_Model, self).__init__(self, args)

        def id_map(val):
            return val

        def match(trna, aars):
            if trna == 0:
                return 1 / 5.0
            if trna & (1 << aars):
                return 1.0
            return 0.0

        def codon_map(trna):
            if 0 <= trna <= 5:
                return 0
            elif 6 <= trna <= 11:
                return 1
            elif 12 <= trna <= 17:
                return 2
            elif 18 <= trna <= 23:
                return 3
            else: #elif 24 <= trna <= 31:
                return 4
        bits = 5
            
        codons = 5
        aas = 5
        trnas = 2**5
        aarss = 5

        msg_mu = .01
        phi = .32768

        bit_mu = .0001

        weights = [20] * aas

        pchem_vals = [0.0, 0.2, 0.4, 0.6, 0.8]

        starting_trnas = [0] * 5 
        starting_aarss = [0, 1, 2, 3, 4]

        trna_ids = ["trna_" + str(i) for i in xrange(trnas)]
        codon_ids = ["codon_" + str(i) for i in xrange(codons)]
        aars_ids = ["aars_" + str(i) for i in xrange(aarss)]

        aa_ids = ["aas_" + str(i) for i in xrange(aas)]
        aa_vals = pchem_vals

        site_ids = ["site_" + str(i) for i in xrange(aas)]
        site_vals = pchem_vals

        self._site_types = Ring_Site_Types(phi, zip(aa_ids, aa_vals),
                                           zip(site_ids, site_vals), weights)

        self._message_mutation_matrix = get_ring_mutation_matrix(codons, msg_mu)
        
        aars_mutation_matrix = get_ring_mutation_matrix(aarss, 0)
        trna_mutation_matrix = get_hamming_distance_mutation_matrix(bits, bit_mu)

        aars_space = AARS_Space(aars_ids, aa_ids, id_map,
                                lambda aars1, aars2: 0, aars_mutation_matrix)

        trna_space = Id_TRNA_Space(trna_ids, codon_ids, match, trna_mutation_matrix)

        #trna_space = TRNA_Space(trna_ids, codon_ids, match, codon_map,
        #                        lambda trna1, trna2: hamming_dist(trna1, trna2, bits), trna_mutation_matrix)

        self._initial_code = Code(starting_trnas, starting_aarss, trna_space, aars_space)

    def get_site_types(self):
        return self._site_types

    def get_message_mutation_matrix(self):
        return self._message_mutation_matrix

    def get_initial_code(self):
        return self._initial_code

class Fifty_Bit_Model(_Model):
    def __init__(self, args, rng):
        super(Fifty_Bit_Model, self).__init__(self, args)

        def frac_hamming_dist(from_, to, length):
            dist = 0
            for i in xrange(length):
                if from_ & (2**i) == to & (2**i):
                    dist += 1

            return dist / float(length)

        def hamming_dist_5(from_, to):
            return frac_hamming_dist(from_, to, 5)

        def id_map(val):
            return val

        bits = 5
        trnas = 2**bits
        aarss = 2**bits
        aas = 32
        mu = .0001
        msg_mu = .1
        pop = 100
        weights = [1] * aas
        
        starting_trnas = [0, 2, 2, 0, 3]
        starting_aarss = [5, 5, 3, 1, 3]

        pchem_vals = [i / float(2**bits) for i in xrange(aas)]

        trna_ids = ["trna_" + str(i) for i in xrange(trnas)]
        codon_ids = ["codon_" + str(i) for i in xrange(trnas)]
        aars_ids = ["aars_" + str(i) for i in xrange(aarss)]

        aa_ids = ["aas_" + str(i) for i in xrange(aas)]
        aa_vals = pchem_vals # sorted([rng.random() for _ in xrange(aas)])

        site_ids = ["site_" + str(i) for i in xrange(aas)]
        site_vals = pchem_vals # sorted([rng.random() for _ in xrange(aas)])

        self._site_types = Ring_Site_Types(args.phi, zip(aa_ids, aa_vals),
                                           zip(site_ids, site_vals), weights)

        self._message_mutation_matrix = get_ring_mutation_matrix(len(trna_ids), msg_mu)

        aars_mutation_matrix = get_hamming_distance_mutation_matrix(bits, mu)
        trna_mutation_matrix = get_hamming_distance_mutation_matrix(bits, mu)

        aars_space = AARS_Space(aars_ids, aa_ids, id_map, lambda aars1, aars2: hamming_dist(aars1, aars2, bits), aars_mutation_matrix)
        trna_space = TRNA_Space(trna_ids, codon_ids, hamming_dist_5, id_map, lambda trna1, trna2: hamming_dist(trna1, trna2, bits), trna_mutation_matrix)
        
        self._initial_code = Code(starting_trnas, starting_aarss, trna_space, aars_space)

    def get_site_types(self):
        return self._site_types

    def get_message_mutation_matrix(self):
        return self._message_mutation_matrix

    def get_initial_code(self):
        return self._initial_code
                

class Test_Bit_Model(_Model):
    def __init__(self, args, rng):
        super(Test_Bit_Model, self).__init__(self, args)

        def frac_hamming_dist(from_, to, length):
            dist = 0
            for i in xrange(length):
                if from_ & (2**i) == to & (2**i):
                    dist += 1

            return dist / float(length)

        def hamming_dist_8(from_, to):
            return frac_hamming_dist(from_, to, 8)

        def id_map(val):
            return val

        trnas = 16
        aarss = 16
        aas = 32
        mu = .0001
        msg_mu = .1
        pop = 100
        weights = [1] * aas
        
        starting_trnas = [5, 5, 3, 0, 0]
        starting_aarss = [5, 5, 3, 0, 0]

        pchem_vals = [i / float(aas) for i in xrange(aas)]

        trna_ids = ["trna_" + str(i) for i in xrange(trnas)]
        codon_ids = ["codon_" + str(i) for i in xrange(trnas)]
        aars_ids = ["aars_" + str(i) for i in xrange(aarss)]

        aa_ids = ["aas_" + str(i) for i in xrange(aas)]
        aa_vals = pchem_vals # sorted([rng.random() for _ in xrange(aas)])

        site_ids = ["site_" + str(i) for i in xrange(aas)]
        site_vals = pchem_vals # sorted([rng.random() for _ in xrange(aas)])

        self._site_types = Ring_Site_Types(args.phi, zip(aa_ids, aa_vals),
                                           zip(site_ids, site_vals), weights)

        self._message_mutation_matrix = get_ring_mutation_matrix(len(trna_ids), msg_mu)

        aars_mutation_matrix = get_hamming_distance_mutation_matrix(int(np.log2(aarss)), mu)
        trna_mutation_matrix = get_hamming_distance_mutation_matrix(int(np.log2(trnas)), mu)

        aars_space = AARS_Space(aars_ids, aa_ids, id_map, lambda aars1, aars2: hamming_dist(aars1, aars2, 3), aars_mutation_matrix)
        trna_space = TRNA_Space(trna_ids, codon_ids, hamming_dist_8, id_map, lambda aars1, aars2: hamming_dist(aars1, aars2, 3), trna_mutation_matrix)
        
        self._initial_code = Code(starting_trnas, starting_aarss, trna_space, aars_space)

    def get_site_types(self):
        return self._site_types

    def get_message_mutation_matrix(self):
        return self._message_mutation_matrix

    def get_initial_code(self):
        return self._initial_code
        

class CMCPy_Test_Model(_Model):
    def __init__(self, args, rng):
        super(Bit_Model, self).__init__(self, args)

        pchem_vals = [0.05,0.15,0.24,0.41,0.44,0.51,0.54,0.79,0.83,0.92]

        site_ids = ["site_" + str(i) for i in pchem_vals]
        aa_ids = ["aa_" + str(i) for i in pchem_vals]
        weights = [1] * len(pchem_vals)

        self._site_types = Ring_Site_Types(.25, zip(aa_ids, pchem_vals),
                                           zip(site_ids, pchem_vals), weights)

        trna_ids = ["trna_" + str(i) for i in xrange(9)]
        codon_ids = ["codon_" + str(i) for i in xrange(9)]
        aars_ids = ["aars_" + str(i) for i in xrange(9)]

        self._message_mutation_matrix = get_ring_mutation_matrix(len(trna_ids), .02)

        aars_space = AARS_Space(aars_ids, aa_ids, aars_aa_map, mutations_between, aars_mutation)
        trna_space = TRNA_Space(trna_ids, codon_ids, trna_aars_map, trna_codon_map,
                                mutations_between, trna_mutation_matrix)

    def get_site_types(self):
        return self._site_types

    def get_message_mutation_matrix(self):
        return self._message_mutation_matrix

    def get_initial_code(self):
        return self._initial_code


class Bit_Model(_Model):
    def __init__(self, args, rng):
        super(Bit_Model, self).__init__(self, args)

        self.trnas = 2**args.trna_length
        self.aarss = 2**args.aars_length

        trna_ids = ["trna_" + str(i) for i in xrange(self.trnas)]
        aars_ids = ["aars_" + str(i) for i in xrange(self.aarss)]

        aas_ids = ["aas_" + str(i) for i in xrange(args.amino_acids)]
        aa_vals = sorted([rng.random() for _ in xrange(args.amino_acids)])

        site_ids = ["site_" + str(i) for i in xrange(args.site_types)]
        site_vals = sorted([rng.random() for _ in xrange(args.site_types)])

        weights = args.site_weights or ['1'] * len(site_ids)
        weights = map(int, list(weights))

        self._site_types = Ring_Site_Types(args.phi, zip(aas_ids, aa_vals),
                                           zip(site_ids, site_vals), weights)

        self._message_mutation_matrix = get_ring_mutation_matrix(len(site_ids), args.message_mu)

        assert len(aa_vals) == len(aars_ids), "The number of AARSs and amino acids must be equal."

        aars_aa_map = np.diag([1] * len(aa_vals))
        aars_mutation_matrix = get_uniform_mutation_matrix(len(aars_ids), args.message_mu)
        
        aars_space = AARS_Space(aars_ids, aars_aa_map, aars_mutation_matrix)

        self.max_len = args.trna_length
        trna_aars_mapping = np.array([[len(trna) - self._hamming_distance(trna, aars)
                                       for aars in map(self.bin_pad, xrange(len(aars_ids)))]
                                      for trna in map(self.bin_pad, xrange(len(trna_ids)))], dtype=np.float)

        row_sums = trna_aars_mapping.sum(axis=1, keepdims=True)
        trna_aars_mapping = trna_aars_mapping / row_sums

        codon_trna_mapping = np.diag([1] * len(trna_ids))

        trna_mutation_matrix = get_uniform_mutation_matrix(len(trna_ids), args.message_mu)
        trna_space = TRNA_Space(trna_ids, trna_aars_mapping, codon_trna_mapping, trna_mutation_matrix)

        self._initial_code = Code([0] * args.trnas, [0] * args.aarss, trna_space, aars_space)

    def get_site_types(self):
        return self._site_types

    def get_message_mutation_matrix(self):
        return self._message_mutation_matrix

    def get_initial_code(self):
        return self._initial_code

    def _hamming_distance(self, arg1, arg2):
        assert len(arg1) == len(arg2), "Objects must be same length."
        return sum(x != y for x, y in zip(arg1, arg2))

    def bin_pad(self, arg): # TODO Fix this hacky thing
        arg = bin(arg)[2:]

        delta = self.max_len - len(arg)
        arg = ''.join(["0"] * delta) + arg

        return arg

        
