from flatlib import const
from dignities_logic import DignitiesLogic

class AspectsLogic:
    def __init__(self):
        self.dignities = DignitiesLogic()
        self.ORBS = {
            const.SUN: 15.0, const.MOON: 12.0, const.MERCURY: 7.0,
            const.VENUS: 7.0, const.MARS: 8.0, const.JUPITER: 9.0,
            const.SATURN: 9.0
        }

    def get_aspects(self, chart, trans_planets, planet_glyphs, trans_aspects):
        """Calculates major aspects using classical orbs."""
        aspects = []
        planets_to_check = [
            const.SUN, const.MOON, const.MERCURY, 
            const.VENUS, const.MARS, const.JUPITER, const.SATURN
        ]
        major_angles = {0: 'Conjunction', 60: 'Sextile', 90: 'Square', 120: 'Trine', 180: 'Opposition'}
        
        for i in range(len(planets_to_check)):
            for j in range(i + 1, len(planets_to_check)):
                p1_id, p2_id = planets_to_check[i], planets_to_check[j]
                p1, p2 = chart.get(p1_id), chart.get(p2_id)
                
                diff = abs(p1.lon - p2.lon)
                if diff > 180: diff = 360 - diff
                
                max_orb = (self.ORBS.get(p1_id, 0) + self.ORBS.get(p2_id, 0)) / 2.0
                
                for angle, name in major_angles.items():
                    if abs(diff - angle) <= max_orb:
                        p1_sym = planet_glyphs.get(p1_id, '')
                        p2_sym = planet_glyphs.get(p2_id, '')
                        aspects.append({
                            'p1': f"{p1_sym} {trans_planets.get(p1_id, p1_id)}",
                            'p2': f"{p2_sym} {trans_planets.get(p2_id, p2_id)}",
                            'aspect': trans_aspects.get(name, name),
                            'orb': f"{round(abs(diff - angle), 2)}°",
                            'reception': self.check_reception(p1_id, p1.lon, p2_id, p2.lon, trans_planets)
                        })
        return aspects

    def check_reception(self, p1_id, p1_lon, p2_id, p2_lon, trans_planets):
        """Checks for Mutual Reception or simple Reception."""
        s1_idx = int(p1_lon // 30)
        s1_const = const.LIST_SIGNS[s1_idx]
        s2_idx = int(p2_lon // 30)
        s2_const = const.LIST_SIGNS[s2_idx]
        
        # P1 is in which dignity of P2?
        p1_in_p2_dom = self.dignities.RULERS[s1_const] == p2_id
        p1_in_p2_exalt = self.dignities.EXALTATIONS.get(s1_const, (None,))[0] == p2_id
        
        # P2 is in which dignity of P1?
        p2_in_p1_dom = self.dignities.RULERS[s2_const] == p1_id
        p2_in_p1_exalt = self.dignities.EXALTATIONS.get(s2_const, (None,))[0] == p1_id
        
        if (p1_in_p2_dom or p1_in_p2_exalt) and (p2_in_p1_dom or p2_in_p1_exalt):
            return "互容 (Mutual Reception)"
        elif p1_in_p2_dom or p1_in_p2_exalt:
            return f"{trans_planets.get(p1_id)} 接納 {trans_planets.get(p2_id)}"
        elif p2_in_p1_dom or p2_in_p1_exalt:
            return f"{trans_planets.get(p2_id)} 接納 {trans_planets.get(p1_id)}"
        return ""
