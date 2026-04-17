ACTIVITY_LEVELS = {
    "Sedentário (sem exercício)": 1.2,
    "Levemente ativo (1-3x/semana)": 1.375,
    "Moderadamente ativo (3-5x/semana)": 1.55,
    "Muito ativo (6-7x/semana)": 1.725,
    "Extremamente ativo (atleta/trabalho físico)": 1.9,
}

GOALS = {
    "Perda de peso rápida (~1kg/semana)": -1000,
    "Perda de peso moderada (~0,5kg/semana)": -500,
    "Manutenção de peso": 0,
    "Ganho de massa leve (~0,25kg/semana)": 250,
    "Ganho de massa moderado (~0,5kg/semana)": 500,
}


def calculate_bmr(weight_kg, height_cm, age, sex):
    if sex == "M":
        return round((10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5, 1)
    return round((10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161, 1)


def calculate_tdee(bmr, activity_factor):
    return round(bmr * activity_factor, 1)


def calculate_goal_kcal(tdee, goal_delta):
    return round(max(tdee + goal_delta, 1200), 1)


def calculate_protein_goal(weight_kg, goal_label):
    if "Perda" in goal_label:
        factor = 2.0
    elif "Ganho" in goal_label:
        factor = 2.2
    else:
        factor = 1.6
    return round(weight_kg * factor, 1)


def classify_bmi(bmi):
    if bmi < 18.5:
        return "Abaixo do peso", "warning"
    elif bmi < 25.0:
        return "Peso normal ✓", "success"
    elif bmi < 30.0:
        return "Sobrepeso", "warning"
    elif bmi < 35.0:
        return "Obesidade Grau I", "danger"
    elif bmi < 40.0:
        return "Obesidade Grau II", "danger"
    return "Obesidade Grau III", "danger"


def get_full_analysis(weight_kg, height_cm, age, sex, activity_label, goal_label):
    activity_factor = ACTIVITY_LEVELS[activity_label]
    goal_delta = GOALS[goal_label]
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_factor)
    goal_kcal = calculate_goal_kcal(tdee, goal_delta)
    protein_goal = calculate_protein_goal(weight_kg, goal_label)
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
    bmi_class, bmi_color = classify_bmi(bmi)
    return {
        "bmr": bmr, "tdee": tdee, "goal_kcal": goal_kcal,
        "protein_goal": protein_goal, "bmi": bmi,
        "bmi_class": bmi_class, "bmi_color": bmi_color,
    }


def calc_nutrients(kcal100, prot100, carb100, fat100, qty):
    f = qty / 100.0
    return (
        round(kcal100 * f, 1),
        round(prot100 * f, 1),
        round(carb100 * f, 1),
        round(fat100 * f, 1)
    )



def calc_grams_for_kcal(kcal_per_100g, target_kcal):
    if kcal_per_100g == 0:
        return 0.0
    return round((target_kcal / kcal_per_100g) * 100, 1)
