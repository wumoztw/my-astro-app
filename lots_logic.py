from flatlib import const

class LotsLogic:
    def calculate_lots(self, chart, houses, is_day, trans_signs, trans_houses):
        """Calculates Part of Fortune and Part of Spirit."""
        asc = chart.get(const.ASC)
        sun = chart.get(const.SUN)
        moon = chart.get(const.MOON)
        
        # Part of Fortune: Asc + Moon - Sun (Day), Asc + Sun - Moon (Night)
        if is_day:
            pof_lon = (asc.lon + moon.lon - sun.lon) % 360
            pos_lon = (asc.lon + sun.lon - moon.lon) % 360
        else:
            pof_lon = (asc.lon + sun.lon - moon.lon) % 360
            pos_lon = (asc.lon + moon.lon - sun.lon) % 360
            
        lots = []
        for name, lon in [("幸運點 (Fortune)", pof_lon), ("精神點 (Spirit)", pos_lon)]:
            sign_idx = int(lon // 30)
            sign_deg = lon % 30
            d = int(sign_deg)
            m = int((sign_deg - d) * 60)
            
            # Find house
            h1_lon = houses[0]['lon']
            diff = (lon - h1_lon) % 360
            house_num = int(diff // 30) + 1
            
            lots.append({
                'name': name,
                'sign': trans_signs.get(const.LIST_SIGNS[sign_idx]),
                'degree': f"{d}°{m}'",
                'house': trans_houses.get(house_num, f"第{house_num}宮")
            })
        return lots

    def get_fixed_stars(self, chart, trans_planets):
        """Checks for conjunctions with major fixed stars."""
        # 2026 Epoch (Approximate modern positions)
        stars = {
            'Regulus (軒轅十四)': 150.1, 
            'Spica (角宿一)': 204.0     
        }
        
        findings = []
        planets = [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS, const.JUPITER, const.SATURN]
        
        for p_id in planets:
            p = chart.get(p_id)
            for s_name, s_lon in stars.items():
                diff = abs(p.lon - s_lon)
                if diff > 180: diff = 360 - diff
                if diff <= 1.5: # 1.5 degree orb for stars
                    findings.append({
                        'planet': trans_planets.get(p_id),
                        'star': s_name,
                        'orb': f"{round(diff, 2)}°"
                    })
        return findings
