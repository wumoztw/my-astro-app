from flatlib import const

class DignitiesLogic:
    # EXALTATIONS
    EXALTATIONS = {
        const.ARIES: (const.SUN, 19),
        const.TAURUS: (const.MOON, 3),
        const.CANCER: (const.JUPITER, 15),
        const.VIRGO: (const.MERCURY, 15),
        const.LIBRA: (const.SATURN, 21),
        const.CAPRICORN: (const.MARS, 28),
        const.PISCES: (const.VENUS, 27)
    }

    # DETRIMENTS (Opposite of Domicile)
    DETRIMENTS = {
        const.ARIES: const.VENUS,
        const.TAURUS: const.MARS,
        const.GEMINI: const.JUPITER,
        const.CANCER: const.SATURN,
        const.LEO: const.SATURN,
        const.VIRGO: const.JUPITER,
        const.LIBRA: const.MARS,
        const.SCORPIO: const.VENUS,
        const.SAGITTARIUS: const.MERCURY,
        const.CAPRICORN: const.MOON,
        const.AQUARIUS: const.SUN,
        const.PISCES: const.MERCURY
    }

    # FALLS (Opposite of Exaltation)
    FALLS = {
        const.ARIES: const.SATURN,
        const.TAURUS: None,
        const.GEMINI: None,
        const.CANCER: const.MARS,
        const.LEO: None,
        const.VIRGO: const.VENUS,
        const.LIBRA: const.SUN,
        const.SCORPIO: const.MOON,
        const.SAGITTARIUS: None,
        const.CAPRICORN: const.JUPITER,
        const.AQUARIUS: None,
        const.PISCES: const.MERCURY
    }

    # TRIPLICITIES (Dorothean: Day, Night, Participating)
    TRIPLICITIES = {
        'Fire': [const.SUN, const.JUPITER, const.SATURN],
        'Earth': [const.VENUS, const.MOON, const.MARS],
        'Air': [const.SATURN, const.MERCURY, const.JUPITER],
        'Water': [const.VENUS, const.MARS, const.MOON]
    }

    SIGN_ELEMENTS = {
        const.ARIES: 'Fire', const.LEO: 'Fire', const.SAGITTARIUS: 'Fire',
        const.TAURUS: 'Earth', const.VIRGO: 'Earth', const.CAPRICORN: 'Earth',
        const.GEMINI: 'Air', const.LIBRA: 'Air', const.AQUARIUS: 'Air',
        const.CANCER: 'Water', const.SCORPIO: 'Water', const.PISCES: 'Water'
    }

    # TERMS (Egyptian)
    TERMS = {
        const.ARIES: [(6, const.JUPITER), (12, const.VENUS), (20, const.MERCURY), (25, const.MARS), (30, const.SATURN)],
        const.TAURUS: [(8, const.VENUS), (14, const.MERCURY), (22, const.JUPITER), (27, const.SATURN), (30, const.MARS)],
        const.GEMINI: [(6, const.MERCURY), (12, const.JUPITER), (17, const.VENUS), (24, const.MARS), (30, const.SATURN)],
        const.CANCER: [(7, const.MARS), (13, const.VENUS), (19, const.MERCURY), (26, const.JUPITER), (30, const.SATURN)],
        const.LEO: [(6, const.JUPITER), (11, const.VENUS), (18, const.SATURN), (24, const.MERCURY), (30, const.MARS)],
        const.VIRGO: [(7, const.MERCURY), (17, const.VENUS), (21, const.JUPITER), (28, const.MARS), (30, const.SATURN)],
        const.LIBRA: [(6, const.SATURN), (14, const.VENUS), (21, const.JUPITER), (28, const.MERCURY), (30, const.MARS)],
        const.SCORPIO: [(7, const.MARS), (11, const.VENUS), (19, const.MERCURY), (24, const.JUPITER), (30, const.SATURN)],
        const.SAGITTARIUS: [(12, const.JUPITER), (17, const.VENUS), (21, const.MERCURY), (26, const.SATURN), (30, const.MARS)],
        const.CAPRICORN: [(7, const.MERCURY), (14, const.JUPITER), (22, const.VENUS), (26, const.SATURN), (30, const.MARS)],
        const.AQUARIUS: [(7, const.SATURN), (13, const.MERCURY), (20, const.JUPITER), (25, const.VENUS), (30, const.MARS)],
        const.PISCES: [(12, const.VENUS), (16, const.JUPITER), (19, const.MERCURY), (28, const.MARS), (30, const.SATURN)]
    }

    # FACES (Chaldean)
    FACES = {
        const.ARIES: [const.MARS, const.SUN, const.VENUS],
        const.TAURUS: [const.MERCURY, const.MOON, const.SATURN],
        const.GEMINI: [const.JUPITER, const.MARS, const.SUN],
        const.CANCER: [const.VENUS, const.MERCURY, const.MOON],
        const.LEO: [const.SATURN, const.JUPITER, const.MARS],
        const.VIRGO: [const.SUN, const.VENUS, const.MERCURY],
        const.LIBRA: [const.MOON, const.SATURN, const.JUPITER],
        const.SCORPIO: [const.MARS, const.SUN, const.VENUS],
        const.SAGITTARIUS: [const.MERCURY, const.MOON, const.SATURN],
        const.CAPRICORN: [const.JUPITER, const.MARS, const.SUN],
        const.AQUARIUS: [const.VENUS, const.MERCURY, const.MOON],
        const.PISCES: [const.SATURN, const.JUPITER, const.MARS]
    }

    RULERS = {
        const.ARIES: const.MARS, const.TAURUS: const.VENUS, const.GEMINI: const.MERCURY,
        const.CANCER: const.MOON, const.LEO: const.SUN, const.VIRGO: const.MERCURY,
        const.LIBRA: const.VENUS, const.SCORPIO: const.MARS, const.SAGITTARIUS: const.JUPITER,
        const.CAPRICORN: const.SATURN, const.AQUARIUS: const.SATURN, const.PISCES: const.JUPITER
    }

    def calculate_essential_dignities(self, p_id, lon, is_day):
        """Calculates Essential Dignities and total score."""
        sign_idx = int(lon // 30)
        sign_deg = lon % 30
        sign_const = const.LIST_SIGNS[sign_idx]
        element = self.SIGN_ELEMENTS[sign_const]
        
        dignities = []
        score = 0
        
        # 1. Domicile (+5)
        if self.RULERS[sign_const] == p_id:
            dignities.append("廟 (Domicile)")
            score += 5
        elif self.DETRIMENTS[sign_const] == p_id:
            dignities.append("陷 (Detriment)")
            score -= 5
            
        # 2. Exaltation (+4)
        exalt = self.EXALTATIONS.get(sign_const)
        if exalt and exalt[0] == p_id:
            dignities.append("旺 (Exaltation)")
            score += 4
        elif self.FALLS.get(sign_const) == p_id:
            dignities.append("弱 (Fall)")
            score -= 4
            
        # 3. Triplicity (+3)
        tri_lords = self.TRIPLICITIES[element]
        if is_day and tri_lords[0] == p_id:
             dignities.append("三分 (Triplicity - Day)")
             score += 3
        elif not is_day and tri_lords[1] == p_id:
             dignities.append("三分 (Triplicity - Night)")
             score += 3
        elif tri_lords[2] == p_id:
             dignities.append("三分 (Triplicity - Part.)")
             score += 3
             
        # 4. Term (+2)
        term_list = self.TERMS[sign_const]
        for max_deg, ruler in term_list:
            if sign_deg < max_deg:
                if ruler == p_id:
                    dignities.append("界 (Term)")
                    score += 2
                break
                
        # 5. Face (+1)
        face_list = self.FACES[sign_const]
        face_idx = int(sign_deg // 10)
        if face_list[face_idx] == p_id:
            dignities.append("面 (Face)")
            score += 1
            
        return {
            'list': dignities,
            'score': score,
            'is_peregrine': score == 0
        }

    def get_accidental_dignities(self, p_id, p_lon, house_num, sun_lon, is_retro):
        """Calculates Accidental states: House strength, Combustion, etc."""
        states = []
        
        # House Strength
        if house_num in [1, 4, 7, 10]:
            states.append("角宮 (Angular)")
        elif house_num in [2, 5, 8, 11]:
            states.append("續宮 (Succedent)")
        else:
            states.append("果宮 (Cadent)")
            
        # Sun Phase (Combustion)
        if p_id != const.SUN:
            diff = abs(p_lon - sun_lon)
            if diff > 180: diff = 360 - diff
            
            if diff <= 0.28: # 17 minutes
                states.append("日心 (Cazimi)")
            elif diff <= 8.5:
                states.append("燃燒 (Combust)")
            elif diff <= 17.0:
                states.append("伏沒 (Under Sunbeams)")
                
        # Retrograde
        if is_retro:
            states.append("逆行 (Retrograde)")
            
        return states
