from datetime import date as date_cls
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from extensions import db
from models import User, Food, DietDay, Meal, MealItem, MEAL_TYPES
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

    goal_kcal = current_user.goal_kcal or 2000
    goal_prot = current_user.protein_goal or 100
    pct_kcal = min(int((total_kcal / goal_kcal) * 100), 100) if goal_kcal else 0
    pct_prot = min(int((total_prot / goal_prot) * 100), 100) if goal_prot else 0

    return render_template(
        "dashboard.html",
        today=today,
        summary=summary,
        meal_types=MEAL_TYPES,
        total_kcal=round(total_kcal, 1),
        total_prot=round(total_prot, 1),
        goal_kcal=goal_kcal,
        goal_prot=goal_prot,
        pct_kcal=pct_kcal,
        pct_prot=pct_prot,
    )


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
        category = request.form.get("category", "Outros")
        unit_name = request.form.get("unit_name", "").strip() or None
        g_per_unit = request.form.get("g_per_unit", "").replace(",", ".")
        g_per_unit = float(g_per_unit) if g_per_unit else None
    except (ValueError, KeyError):
        flash("Preencha todos os campos corretamente.", "danger")
        return redirect(url_for("main.foods"))

    food = Food(name=name, kcal_per_100g=kcal,
                protein_per_100g=protein, category=category,
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

    target.name = request.form["name"].strip()
    target.kcal_per_100g = float(request.form["kcal"].replace(",", "."))
    target.protein_per_100g = float(request.form["protein"].replace(",", "."))
    target.category = request.form.get("category", "Outros")
    
    unit_name = request.form.get("unit_name", "").strip() or None
    g_per_unit = request.form.get("g_per_unit", "").replace(",", ".")
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
    day = DietDay.query.filter_by(user_id=current_user.id, date=selected_date).first()
    summary = _build_day_summary(day)
    total_kcal = round(sum(m["total_kcal"] for m in summary.values()), 1)
    total_prot = round(sum(m["total_prot"] for m in summary.values()), 1)

    all_foods = Food.query.filter(
        or_(Food.user_id == current_user.id, Food.user_id == None)
    ).order_by(Food.name).all()

    return render_template(
        "meals.html",
        selected_date=selected_date,
        summary=summary,
        meal_types=MEAL_TYPES,
        foods=all_foods,
        total_kcal=total_kcal,
        total_prot=total_prot,
        goal_kcal=current_user.goal_kcal or 2000,
        goal_prot=current_user.protein_goal or 100,
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

    kcal, prot = calc_nutrients(food.kcal_per_100g, food.protein_per_100g, quantity_g)
    flash(f"✅ {quantity_g}g de {food.name} adicionado → {kcal} kcal | {prot}g prot.", "success")
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


# ─── API JSON ─────────────────────────────────────────────────────────────────

@main_bp.route("/api/calc")
@login_required
def api_calc():
    try:
        kcal100 = float(request.args["kcal100"])
        prot100 = float(request.args["prot100"])
        qty = float(request.args.get("qty", 100))
    except (ValueError, KeyError):
        return jsonify({"error": "invalid"}), 400
    kcal, prot = calc_nutrients(kcal100, prot100, qty)
    return jsonify({"kcal": kcal, "prot": prot})


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
        for item in meal.items:
            kcal, prot = calc_nutrients(
                item.food.kcal_per_100g, item.food.protein_per_100g, item.quantity_g
            )
            meal_kcal += kcal
            meal_prot += prot
            items_data.append({
                "id": item.id,
                "name": item.food.name,
                "quantity_g": item.quantity_g,
                "kcal": kcal,
                "prot": prot,
            })
        summary[meal.meal_type] = {
            "items": items_data,
            "total_kcal": round(meal_kcal, 1),
            "total_prot": round(meal_prot, 1),
        }
    return summary
