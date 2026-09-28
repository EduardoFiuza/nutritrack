from datetime import date as date_cls, datetime, timedelta
import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from models import User, Food, DietDay, Meal, MealItem, MEAL_TYPES, FavoriteMeal, FavoriteMealItem
from calculators import (
    ACTIVITY_LEVELS, GOALS, get_full_analysis,
    calc_nutrients, calc_grams_for_kcal,
)

main_bp = Blueprint("main", __name__)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@main_bp.route("/")
@login_required
def dashboard():
    today = str(date_cls.today())
    day = DietDay.query.filter_by(user_id=current_user.id, date=today).first()
    summary = _build_day_summary(day)
    total_kcal = sum(m["total_kcal"] for m in summary.values())
    total_prot = sum(m["total_prot"] for m in summary.values())
    total_carb = sum(m["total_carb"] for m in summary.values())
    total_fat = sum(m["total_fat"] for m in summary.values())

    goal_kcal = current_user.goal_kcal or 2000
    goal_prot = current_user.protein_goal or 100
    # Metas padrão simplificadas para Carb e Gord caso não existam no perfil
    goal_carb = goal_kcal * 0.5 / 4  # 50% kcal
    goal_fat = goal_kcal * 0.3 / 9   # 30% kcal

    pct_kcal = min(int((total_kcal / goal_kcal) * 100), 100) if goal_kcal else 0
    pct_prot = min(int((total_prot / goal_prot) * 100), 100) if goal_prot else 0

    # ── Avatar Corporal & Gordura ──
    u = current_user
    bmi = None
    bf_pct = None
    body_status = "Perfil não preenchido"
    body_color = "var(--dim)"
    belly_radius = 24
    is_male = (u.sex or "M").upper() == "M"
    if u.weight_kg and u.height_cm:
        h_m = u.height_cm / 100.0
        bmi = round(u.weight_kg / (h_m * h_m), 1)
        age = u.age or 25
        sex_factor = 1 if is_male else 0
        bf_pct = round((1.20 * bmi) + (0.23 * age) - (10.8 * sex_factor) - 5.4, 1)
        bf_pct = max(5.0, min(bf_pct, 55.0))
        
        if is_male:
            if bf_pct < 13:
                body_status = "Atlético / Definido"
                body_color = "var(--green)"
            elif bf_pct < 20:
                body_status = "Em Forma / Saudável"
                body_color = "var(--green)"
            elif bf_pct < 25:
                body_status = "Gordura Moderada"
                body_color = "var(--yellow)"
            else:
                body_status = "Sobrepeso / Em Redução"
                body_color = "#ff6584"
        else:
            if bf_pct < 20:
                body_status = "Atlética / Definida"
                body_color = "var(--green)"
            elif bf_pct < 27:
                body_status = "Em Forma / Saudável"
                body_color = "var(--green)"
            elif bf_pct < 32:
                body_status = "Gordura Moderada"
                body_color = "var(--yellow)"
            else:
                body_status = "Sobrepeso / Em Redução"
                body_color = "#ff6584"

        belly_radius = int(max(16, min(48, 16 + (bmi - 18.5) * 2.2)))

    return render_template(
        "dashboard.html",
        today=today,
        summary=summary,
        meal_types=MEAL_TYPES,
        total_kcal=round(total_kcal, 1),
        total_prot=round(total_prot, 1),
        total_carb=round(total_carb, 1),
        total_fat=round(total_fat, 1),
        goal_kcal=goal_kcal,
        goal_prot=goal_prot,
        goal_carb=round(goal_carb, 1),
        goal_fat=round(goal_fat, 1),
        pct_kcal=pct_kcal,
        pct_prot=pct_prot,
        bmi=bmi,
        bf_pct=bf_pct,
        body_status=body_status,
        body_color=body_color,
        belly_radius=belly_radius,
        is_male=is_male,
    )


@main_bp.route("/user/update-weight", methods=["POST"])
@login_required
def update_weight():
    try:
        new_weight = float(request.form["weight_kg"].replace(",", "."))
        if 20 < new_weight < 350:
            diff = round(new_weight - (current_user.weight_kg or new_weight), 1)
            current_user.weight_kg = new_weight

            # Recalcular metas se perfil preenchido
            if current_user.height_cm and current_user.age and current_user.activity_level and current_user.goal:
                res = get_full_analysis(
                    current_user.weight_kg, current_user.height_cm,
                    current_user.age, current_user.sex or "M",
                    current_user.activity_level, current_user.goal
                )
                current_user.goal_kcal = res["goal_kcal"]
                current_user.protein_goal = res["protein_goal"]

            db.session.commit()
            if diff < 0:
                flash(f"🎉 Peso atualizado: {new_weight} kg ({abs(diff)} kg a menos! Parabéns!)", "success")
            elif diff > 0:
                flash(f"Peso atualizado: {new_weight} kg (+{diff} kg).", "info")
            else:
                flash(f"Peso atualizado: {new_weight} kg.", "success")
    except (ValueError, KeyError):
        flash("Valor de peso inválido.", "danger")

    return redirect(request.referrer or url_for("main.dashboard"))


@main_bp.route("/user/set-gender", methods=["POST"])
@login_required
def set_gender():
    g = request.form.get("sex", "M").upper()
    if g in ["M", "F"]:
        current_user.sex = g
        if current_user.weight_kg and current_user.height_cm and current_user.age and current_user.activity_level and current_user.goal:
            res = get_full_analysis(
                current_user.weight_kg, current_user.height_cm,
                current_user.age, current_user.sex,
                current_user.activity_level, current_user.goal
            )
            current_user.goal_kcal = res["goal_kcal"]
            current_user.protein_goal = res["protein_goal"]
        db.session.commit()
    return jsonify({"success": True, "sex": current_user.sex})




# ─── BMR ──────────────────────────────────────────────────────────────────────

@main_bp.route("/bmr", methods=["GET", "POST"])
@login_required
def bmr():
    result = None
    u = current_user

    if request.method == "POST":
        try:
            weight = float(request.form["weight"].replace(",", "."))
            height = float(request.form["height"].replace(",", "."))
            age = int(request.form["age"])
            sex = request.form["sex"]
            activity = request.form["activity"]
            goal = request.form["goal"]
        except (ValueError, KeyError):
            flash("Verifique os valores inseridos.", "danger")
            return redirect(url_for("main.bmr"))

        if (
            not math.isfinite(weight)
            or not math.isfinite(height)
            or not 30 <= weight <= 300
            or not 100 <= height <= 250
            or not 10 <= age <= 120
            or sex not in ("M", "F")
            or activity not in ACTIVITY_LEVELS
            or goal not in GOALS
        ):
            flash("Verifique os valores inseridos.", "danger")
            return redirect(url_for("main.bmr"))

        result = get_full_analysis(weight, height, age, sex, activity, goal)

        # Salvar perfil
        u.weight_kg = weight
        u.height_cm = height
        u.age = age
        u.sex = sex
        u.activity_level = activity
        u.goal = goal
        u.goal_kcal = result["goal_kcal"]
        u.protein_goal = result["protein_goal"]
        db.session.commit()
        flash("Perfil salvo com sucesso! ✅", "success")

    return render_template(
        "bmr.html",
        result=result,
        activity_levels=list(ACTIVITY_LEVELS.keys()),
        goals=list(GOALS.keys()),
        user=u,
    )


# ─── Foods ────────────────────────────────────────────────────────────────────

@main_bp.route("/foods")
@login_required
def foods():
    search = request.args.get("q", "")
    category = request.args.get("category", "")

    query = Food.query.filter(
        or_(Food.user_id == current_user.id, Food.user_id == None)
    )
    if search:
        query = query.filter(Food.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Food.category == category)
    food_list = query.order_by(Food.name).all()

    categories = db.session.query(Food.category).filter(
        or_(Food.user_id == current_user.id, Food.user_id == None)
    ).distinct().order_by(Food.category).all()
    categories = [c[0] for c in categories]

    return render_template("foods.html", foods=food_list,
                           categories=categories, search=search,
                           selected_cat=category)


@main_bp.route("/foods/add", methods=["POST"])
@login_required
def add_food():
    try:
        name = request.form["name"].strip()
        kcal = float(request.form["kcal"].replace(",", "."))
        protein = float(request.form["protein"].replace(",", "."))
        carbs = float(request.form.get("carbs", "0").replace(",", "."))
        fat = float(request.form.get("fat", "0").replace(",", "."))
        category = request.form.get("category", "Outros")
        unit_name = request.form.get("unit_name", "").strip() or None
        g_per_unit = request.form.get("g_per_unit", "").replace(",", ".")
        g_per_unit = float(g_per_unit) if g_per_unit else None
    except (ValueError, KeyError):
        flash("Preencha todos os campos corretamente.", "danger")
        return redirect(url_for("main.foods"))

    if (
        not name
        or not all(math.isfinite(value) and value >= 0 for value in (kcal, protein, carbs, fat))
        or (g_per_unit is not None and (not math.isfinite(g_per_unit) or g_per_unit <= 0))
    ):
        flash("Preencha os dados do alimento com valores válidos.", "danger")
        return redirect(url_for("main.foods"))

    food = Food(name=name, kcal_per_100g=kcal,
                protein_per_100g=protein, 
                carbs_per_100g=carbs,
                fat_per_100g=fat,
                category=category,
                unit_name=unit_name, g_per_unit=g_per_unit,
                user_id=current_user.id)
    db.session.add(food)
    db.session.commit()
    flash(f"'{name}' adicionado com sucesso! ✅", "success")
    return redirect(url_for("main.foods"))



@main_bp.route("/foods/delete/<int:food_id>", methods=["POST"])
@login_required
def delete_food(food_id):
    food = Food.query.filter_by(id=food_id, user_id=current_user.id).first_or_404()
    db.session.delete(food)
    db.session.commit()
    flash(f"'{food.name}' removido.", "info")
    return redirect(url_for("main.foods"))


@main_bp.route("/foods/edit/<int:food_id>", methods=["POST"])
@login_required
def edit_food(food_id):
    # Busca o alimento original
    food = Food.query.filter(
        Food.id == food_id,
        or_(Food.user_id == current_user.id, Food.user_id == None)
    ).first_or_404()

    try:
        name = request.form["name"].strip()
        kcal = float(request.form["kcal"].replace(",", "."))
        protein = float(request.form["protein"].replace(",", "."))
        unit_name = request.form.get("unit_name", "").strip() or None
        g_per_unit = request.form.get("g_per_unit", "").replace(",", ".")
        g_per_unit = float(g_per_unit) if g_per_unit else None
    except (ValueError, KeyError):
        flash("Preencha todos os campos corretamente.", "danger")
        return redirect(url_for("main.foods"))

    if (
        not name
        or not all(math.isfinite(value) and value >= 0 for value in (kcal, protein))
        or (g_per_unit is not None and (not math.isfinite(g_per_unit) or g_per_unit <= 0))
    ):
        flash("Preencha os dados do alimento com valores válidos.", "danger")
        return redirect(url_for("main.foods"))

    # Se for global (None), criamos uma CÓPIA pessoal para não afetar os outros
    # Se for do usuário, editamos o original.
    is_global = (food.user_id is None)
    
    if is_global:
        new_food = Food(user_id=current_user.id)
        target = new_food
        db.session.add(new_food)
        flash(f"'{food.name}' personalizado e salvo na sua lista! ✨", "success")
    else:
        target = food
        flash("Alimento atualizado! ✅", "success")

    target.name = name
    target.kcal_per_100g = kcal
    target.protein_per_100g = protein
    target.category = request.form.get("category", "Outros")

    target.unit_name = unit_name
    target.g_per_unit = float(g_per_unit) if g_per_unit else None
    
    db.session.commit()
    return redirect(url_for("main.foods"))


# ─── Meals ────────────────────────────────────────────────────────────────────

@main_bp.route("/meals")
@login_required
def meals():
    today = str(date_cls.today())
    selected_date = request.args.get("date", today)
    try:
        current_dt = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        selected_date = today
        current_dt = date_cls.today()

    prev_date = (current_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (current_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    formatted_date = current_dt.strftime("%d/%m/%Y")

    day = DietDay.query.filter_by(user_id=current_user.id, date=selected_date).first()
    summary = _build_day_summary(day)
    total_kcal = round(sum(m["total_kcal"] for m in summary.values()), 1)
    total_prot = round(sum(m["total_prot"] for m in summary.values()), 1)
    total_carb = round(sum(m["total_carb"] for m in summary.values()), 1)
    total_fat = round(sum(m["total_fat"] for m in summary.values()), 1)

    all_foods = Food.query.filter(
        or_(Food.user_id == current_user.id, Food.user_id == None)
    ).order_by(Food.name).all()

    # Refeições Favoritas do usuário
    user_favorites = FavoriteMeal.query.filter_by(user_id=current_user.id).order_by(FavoriteMeal.name).all()
    favorites_data = []
    for fav in user_favorites:
        fav_kcal = 0
        fav_prot = 0
        items_summary = []
        for it in fav.items:
            k, p, c, f = calc_nutrients(
                it.food.kcal_per_100g, it.food.protein_per_100g,
                it.food.carbs_per_100g, it.food.fat_per_100g,
                it.quantity_g
            )
            fav_kcal += k
            fav_prot += p
            items_summary.append(f"{it.food.name} ({int(it.quantity_g)}g)")
        favorites_data.append({
            "id": fav.id,
            "name": fav.name,
            "meal_type": fav.meal_type,
            "total_kcal": round(fav_kcal, 1),
            "total_prot": round(fav_prot, 1),
            "items_count": len(fav.items),
            "items_text": ", ".join(items_summary)
        })

    goal_kcal = current_user.goal_kcal or 2000
    return render_template(
        "meals.html",
        selected_date=selected_date,
        today=today,
        prev_date=prev_date,
        next_date=next_date,
        formatted_date=formatted_date,
        summary=summary,
        meal_types=MEAL_TYPES,
        foods=all_foods,
        favorites=favorites_data,
        total_kcal=total_kcal,
        total_prot=total_prot,
        total_carb=total_carb,
        total_fat=total_fat,
        goal_kcal=goal_kcal,
        goal_prot=current_user.protein_goal or 100,
        goal_carb=round(goal_kcal * 0.5 / 4, 1),
        goal_fat=round(goal_kcal * 0.3 / 9, 1),
    )



@main_bp.route("/meals/add", methods=["POST"])
@login_required
def add_meal_item():
    try:
        selected_date = request.form["date"]
        meal_type = request.form["meal_type"]
        food_id = int(request.form["food_id"])
        quantity_g = float(request.form["quantity_g"].replace(",", "."))
    except (ValueError, KeyError):
        flash("Preencha todos os campos.", "danger")
        return redirect(url_for("main.meals"))

    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        flash("Data inválida.", "danger")
        return redirect(url_for("main.meals"))

    if (
        meal_type not in MEAL_TYPES
        or not math.isfinite(quantity_g)
        or quantity_g <= 0
    ):
        flash("Refeição ou quantidade inválida.", "danger")
        return redirect(url_for("main.meals", date=selected_date))

    # Verificar que o alimento existe e pertence ao usuário ou é global
    food = Food.query.filter(
        Food.id == food_id,
        or_(Food.user_id == current_user.id, Food.user_id == None)
    ).first_or_404()

    day = DietDay.query.filter_by(user_id=current_user.id, date=selected_date).first()
    if not day:
        day = DietDay(user_id=current_user.id, date=selected_date)
        db.session.add(day)
        db.session.flush()

    meal = Meal.query.filter_by(diet_day_id=day.id, meal_type=meal_type).first()
    if not meal:
        meal = Meal(diet_day_id=day.id, meal_type=meal_type)
        db.session.add(meal)
        db.session.flush()

    item = MealItem(meal_id=meal.id, food_id=food.id, quantity_g=quantity_g)
    db.session.add(item)
    db.session.commit()

    kcal, prot, carb, fat = calc_nutrients(
        food.kcal_per_100g, food.protein_per_100g, 
        food.carbs_per_100g, food.fat_per_100g, quantity_g
    )
    flash(f"✅ {quantity_g}g de {food.name} adicionado!", "success")
    return redirect(url_for("main.meals", date=selected_date))



@main_bp.route("/meals/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_meal_item(item_id):
    item = MealItem.query.join(Meal).join(DietDay).filter(
        MealItem.id == item_id,
        DietDay.user_id == current_user.id
    ).first_or_404()
    
    db.session.delete(item)
    db.session.commit()
    
    if request.headers.get('Accept') == 'application/json' or request.is_json:
        return jsonify({"success": True, "message": "Item removido."})
        
    flash("Item removido.", "info")
    return redirect(request.referrer or url_for("main.meals"))


# ─── Refeições Favoritas ──────────────────────────────────────────────────────

@main_bp.route("/favorites/save/<int:meal_id>", methods=["POST"])
@login_required
def save_favorite(meal_id):
    meal = Meal.query.join(DietDay).filter(
        Meal.id == meal_id,
        DietDay.user_id == current_user.id
    ).first_or_404()

    if not meal.items:
        flash("Esta refeição não tem alimentos para salvar.", "warning")
        return redirect(request.referrer or url_for("main.meals"))

    fav_name = request.form.get("name", "").strip() or f"{meal.meal_type} Favorito"
    selected_date = request.form.get("date", str(date_cls.today()))

    fav = FavoriteMeal(user_id=current_user.id, name=fav_name, meal_type=meal.meal_type)
    db.session.add(fav)
    db.session.flush()

    for it in meal.items:
        fav_item = FavoriteMealItem(favorite_meal_id=fav.id, food_id=it.food_id, quantity_g=it.quantity_g)
        db.session.add(fav_item)

    db.session.commit()
    flash(f"Refeição salva como favorita '{fav_name}'! ⭐", "success")
    return redirect(url_for("main.meals", date=selected_date))


@main_bp.route("/favorites/apply/<int:fav_id>", methods=["POST"])
@login_required
def apply_favorite(fav_id):
    fav = FavoriteMeal.query.filter_by(id=fav_id, user_id=current_user.id).first_or_404()
    selected_date = request.form.get("date", str(date_cls.today()))
    target_meal_type = request.form.get("meal_type", fav.meal_type)

    day = DietDay.query.filter_by(user_id=current_user.id, date=selected_date).first()
    if not day:
        day = DietDay(user_id=current_user.id, date=selected_date)
        db.session.add(day)
        db.session.flush()

    meal = Meal.query.filter_by(diet_day_id=day.id, meal_type=target_meal_type).first()
    if not meal:
        meal = Meal(diet_day_id=day.id, meal_type=target_meal_type)
        db.session.add(meal)
        db.session.flush()

    for fit in fav.items:
        new_item = MealItem(meal_id=meal.id, food_id=fit.food_id, quantity_g=fit.quantity_g)
        db.session.add(new_item)

    db.session.commit()
    flash(f"Refeição favorita '{fav.name}' adicionada ao {target_meal_type}! ⭐", "success")
    return redirect(url_for("main.meals", date=selected_date))


@main_bp.route("/favorites/delete/<int:fav_id>", methods=["POST"])
@login_required
def delete_favorite(fav_id):
    fav = FavoriteMeal.query.filter_by(id=fav_id, user_id=current_user.id).first_or_404()
    fav_name = fav.name
    db.session.delete(fav)
    db.session.commit()
    flash(f"Favorito '{fav_name}' removido.", "info")
    return redirect(request.referrer or url_for("main.meals"))



# ─── API JSON ─────────────────────────────────────────────────────────────────

@main_bp.route("/api/calc")
@login_required
def api_calc():
    try:
        kcal100 = float(request.args["kcal100"])
        prot100 = float(request.args["prot100"])
        carb100 = float(request.args.get("carb100", 0))
        fat100 = float(request.args.get("fat100", 0))
        qty = float(request.args.get("qty", 100))
    except (ValueError, KeyError):
        return jsonify({"error": "invalid"}), 400
    kcal, prot, carb, fat = calc_nutrients(kcal100, prot100, carb100, fat100, qty)
    return jsonify({"kcal": kcal, "prot": prot, "carb": carb, "fat": fat})



@main_bp.route("/api/foods")
@login_required
def api_foods():
    q = request.args.get("q", "")
    foods = Food.query.filter(
        or_(Food.user_id == current_user.id, Food.user_id == None),
        Food.name.ilike(f"%{q}%")
    ).order_by(Food.name).limit(20).all()
    return jsonify([{
        "id": f.id, "name": f.name,
        "kcal": f.kcal_per_100g, "prot": f.protein_per_100g,
        "carb": f.carbs_per_100g, "fat": f.fat_per_100g,
        "category": f.category,
        "unit_name": f.unit_name,
        "g_per_unit": f.g_per_unit
    } for f in foods])



# ─── Helper ───────────────────────────────────────────────────────────────────

def _build_day_summary(day):
    summary = {}
    if not day:
        return summary
    for meal in day.meals:
        items_data = []
        meal_kcal = 0.0
        meal_prot = 0.0
        meal_carb = 0.0
        meal_fat = 0.0
        for item in meal.items:
            kcal, prot, carb, fat = calc_nutrients(
                item.food.kcal_per_100g, item.food.protein_per_100g,
                item.food.carbs_per_100g, item.food.fat_per_100g,
                item.quantity_g
            )
            meal_kcal += kcal
            meal_prot += prot
            meal_carb += carb
            meal_fat += fat
            items_data.append({
                "id": item.id,
                "name": item.food.name,
                "quantity_g": item.quantity_g,
                "kcal": kcal,
                "prot": prot,
                "carb": carb,
                "fat": fat,
            })
        summary[meal.meal_type] = {
            "meal_id": meal.id,
            "items": items_data,
            "total_kcal": round(meal_kcal, 1),
            "total_prot": round(meal_prot, 1),
            "total_carb": round(meal_carb, 1),
            "total_fat": round(meal_fat, 1),
        }

    return summary


# ─── Histórico (Semanal e Mensal) ─────────────────────────────────────────────

@main_bp.route("/history")
@login_required
def history():
    view_type = request.args.get("view", "week")
    today_dt = date_cls.today()

    goal_kcal = current_user.goal_kcal or 2000
    goal_prot = current_user.protein_goal or 100
    goal_carb = round(goal_kcal * 0.5 / 4, 1)
    goal_fat = round(goal_kcal * 0.3 / 9, 1)

    # 1. Visão Semanal (7 dias)
    ref_date_str = request.args.get("ref_date", str(today_dt))
    try:
        ref_dt = datetime.strptime(ref_date_str, "%Y-%m-%d").date()
    except ValueError:
        ref_dt = today_dt

    weekdays_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    days_data = []

    for i in range(6, -1, -1):
        d = ref_dt - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        diet_day = DietDay.query.filter_by(user_id=current_user.id, date=d_str).first()
        summary = _build_day_summary(diet_day)
        d_kcal = round(sum(m["total_kcal"] for m in summary.values()), 1)
        d_prot = round(sum(m["total_prot"] for m in summary.values()), 1)
        d_carb = round(sum(m["total_carb"] for m in summary.values()), 1)
        d_fat = round(sum(m["total_fat"] for m in summary.values()), 1)

        pct_kcal = min(int((d_kcal / goal_kcal) * 100), 100) if goal_kcal else 0
        pct_prot = min(int((d_prot / goal_prot) * 100), 100) if goal_prot else 0

        days_data.append({
            "date": d_str,
            "formatted_date": d.strftime("%d/%m"),
            "weekday": weekdays_pt[d.weekday()],
            "is_today": (d == today_dt),
            "total_kcal": d_kcal,
            "total_prot": d_prot,
            "total_carb": d_carb,
            "total_fat": d_fat,
            "pct_kcal": pct_kcal,
            "pct_prot": pct_prot,
            "meal_count": len(summary),
        })

    # 2. Visão Mensal
    selected_month = request.args.get("month", today_dt.strftime("%Y-%m"))
    month_days = DietDay.query.filter(
        DietDay.user_id == current_user.id,
        DietDay.date.like(f"{selected_month}%")
    ).order_by(DietDay.date.desc()).all()

    month_records = []
    month_total_kcal = 0
    month_total_prot = 0
    days_with_records = 0

    for md in month_days:
        s = _build_day_summary(md)
        if s:
            k = round(sum(m["total_kcal"] for m in s.values()), 1)
            p = round(sum(m["total_prot"] for m in s.values()), 1)
            c = round(sum(m["total_carb"] for m in s.values()), 1)
            f = round(sum(m["total_fat"] for m in s.values()), 1)
            if k > 0 or p > 0:
                days_with_records += 1
                month_total_kcal += k
                month_total_prot += p
                dt_obj = datetime.strptime(md.date, "%Y-%m-%d").date()
                month_records.append({
                    "date": md.date,
                    "formatted_date": dt_obj.strftime("%d/%m/%Y"),
                    "weekday": weekdays_pt[dt_obj.weekday()],
                    "total_kcal": k,
                    "total_prot": p,
                    "total_carb": c,
                    "total_fat": f,
                    "pct_kcal": min(int((k / goal_kcal) * 100), 100) if goal_kcal else 0,
                    "meal_count": len(s)
                })

    avg_kcal = round(month_total_kcal / days_with_records, 1) if days_with_records > 0 else 0
    avg_prot = round(month_total_prot / days_with_records, 1) if days_with_records > 0 else 0

    return render_template(
        "history.html",
        view_type=view_type,
        days_data=days_data,
        ref_date=str(ref_dt),
        prev_week=(ref_dt - timedelta(days=7)).strftime("%Y-%m-%d"),
        next_week=(ref_dt + timedelta(days=7)).strftime("%Y-%m-%d"),
        selected_month=selected_month,
        month_records=month_records,
        days_with_records=days_with_records,
        avg_kcal=avg_kcal,
        avg_prot=avg_prot,
        goal_kcal=goal_kcal,
        goal_prot=goal_prot,
        goal_carb=goal_carb,
        goal_fat=goal_fat,
        today=str(today_dt)
    )

