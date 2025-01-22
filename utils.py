
def calculate_water(weight, activity, temp):
    base = weight * 30
    activity_water = (activity // 30) * 500
    temp_water = 500 if (temp > 25 and temp < 30) else 750 if (temp > 30 and temp < 35) else 1000 if (temp > 35) else 0

    return base + activity_water + temp_water

def calculate_calories(weight, height, age, activity, MET):
    base_calories = 10 * weight + 6.25 * height - 5 * age
    extra_calories = (activity) * (MET * 3.5 * weight) / 200
    return base_calories + extra_calories

