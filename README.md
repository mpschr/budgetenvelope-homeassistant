# Budget Envelope

This is an integration ment for making your budgeting transparent by displaying the states of your how much money is left in your envelopes, i.e. categories where money is put into monthly and then drawn from.

Input is a json file calculated with the https://github.com/mpschr/budget-envelopes library or produced manually by you. 


# Configuration

Allow home assisstant acces to your home directory

e.g. :
```
homeassistant:
  allowlist_external_dirs:
    - '/config/data'
```

if `config` is a default for home assisstant - if you have another name, adapt the example

- Install via HACS, custom repository-download (details to follow) 
- Follow configuration steps

# Example Device

Below is what a budget envelope in home assistant look like. The example is the Charging budget for the car. What is not visibile this envelope is a sub-envelope of the `car` envelope.

![Budget Envelope Device](budgetenvelope-device.png?raw=true "Budget Envelope Device")

Following sensors are made available (if supplied by the the json file):

- `Charging`: State of Balance.
- `Charging %`: State of Balance in % - referring to the monthly budget.
- `Charging Budget`: The actual budget of the current month, including adjustments(s), but not including the carryover.
- `Charging Adjustment`: Adjustments made to the budget envelope. E.g. transfers from another envelope or one-off adjustments for the current month.
- `Charging Carryover`: The carryover (leftover money) in the envelope from last month. Negative values allowed, altough not recommended ;).

# Attribution

<a href="https://www.flaticon.com/free-icons/salary" title="salary icons">Salary icons created by nawicon - Flaticon</a>