from datetime import date, datetime
import pandas as pd
from time_lords_logic import TimeLordsLogic

def test_firdaria_future_date():
    logic = TimeLordsLogic()
    # Mocking birth_dt_str as the future date requested by user
    birth_date_str = "2026/02/20"
    birth_date = date(2026, 2, 20)
    is_day = True
    
    print(f"Testing Firdaria with birth_date: {birth_date_str}")
    try:
        # Pass the future date as current_date (which simulates the Horary case)
        result = logic.get_firdaria_data(birth_date_str, is_day, current_date=birth_date)
        
        active = result['active']
        print(f"Active Major: {active['major']}")
        print(f"Active Minor: {active['minor']}")
        print(f"Active End: {active['end']}")
        
        if active['major'] is not None:
            print("SUCCESS: Active period found for future date.")
            # Test strftime compatibility
            print(f"Formatted End Date: {active['end'].strftime('%Y/%m/%d')}")
        else:
            print("FAILURE: Active period is None.")
            
    except Exception as e:
        print(f"FAILURE: Exception occurred: {e}")

if __name__ == "__main__":
    test_firdaria_future_date()
