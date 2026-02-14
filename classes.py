from dataclasses import dataclass, field
from datetime import datetime

def default_claimed():
    return {"May2025": False, "Jan2026": False}

def default_voucher():
    return {
        "May2025": {"2": 0, "5": 0, "10": 0},
        "Jan2026": {"2": 0, "5": 0, "10": 0},
    }

@dataclass
class Household: 
    Household_ID:str
    Registration_Date: str  
    Postal_Code: str 
    Unit_No: str 
    #status of whether the two tranches have been claimed,set default
    # field let us configure how a class attribute behave, for the claimed attribute, we set it as a dictionary
    # when a new object is created, we set it to the default dictionary
    Claimed: dict = field(default_factory=default_claimed)
    # number of vouchers in each household
    # same logic as claimed attribute
    Voucher: dict = field(default_factory=default_voucher)

    # voucher code for household
    Voucher_Code_Seq: int = 1
   
    # calculate the total balance of the household
    def household_total_balance(self):
      total= 0
      for tranche in ("May2025", "Jan2026"):
        vouchers = self.Voucher[tranche]
        total += 2 * vouchers["2"] + 5 * vouchers["5"] + 10 * vouchers["10"]
      return total


