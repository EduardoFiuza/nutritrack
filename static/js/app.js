// ─── Navbar hamburger ────────────────────────────────────────────────────────
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('nav-menu');
if (hamburger && navMenu) {
  hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('open');
  });
  document.addEventListener('click', e => {
    if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
      navMenu.classList.remove('open');
    }
  });
}

// ─── Auto-dismiss alerts ─────────────────────────────────────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.transition = 'opacity .5s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 500);
  }, 4000);
});

// ─── Food search autocomplete (meals page) ────────────────────────────────────
const foodSearchInput = document.getElementById('food-search');
const foodIdInput = document.getElementById('food_id');
const foodDropdown = document.getElementById('food-dropdown');
const qtyInput = document.getElementById('quantity_g');
const previewDiv = document.getElementById('add-preview');

let selectedFood = null;

if (foodSearchInput) {
  foodSearchInput.addEventListener('input', async () => {
    const q = foodSearchInput.value.trim();
    if (q.length < 1) { foodDropdown.innerHTML = ''; foodDropdown.style.display='none'; return; }

    const res = await fetch(`/api/foods?q=${encodeURIComponent(q)}`);
    const foods = await res.json();

    foodDropdown.innerHTML = '';
    if (foods.length === 0) { foodDropdown.style.display='none'; return; }

    foods.forEach(f => {
      const item = document.createElement('div');
      item.className = 'dropdown-item';
      let unitInfo = f.unit_name ? `<span class="badge badge-purple">${f.unit_name}</span>` : '';
      item.innerHTML = `<span class="di-name">${f.name} ${unitInfo}</span>
        <span class="di-stats">
            <span style="color:var(--yellow)">🔥 ${f.kcal}</span> | 
            <span style="color:var(--prot)">💪 ${f.prot}g</span> | 
            <span style="color:var(--carb)">🍞 ${f.carb}g</span> | 
            <span style="color:var(--fat)">🥑 ${f.fat}g</span>
        </span>`;
      item.addEventListener('click', () => {
        window.selectedFood = f;
        foodSearchInput.value = f.name;
        foodIdInput.value = f.id;
        foodDropdown.style.display = 'none';
        
        const measureSelect = document.getElementById('measure-select');
        if (measureSelect) {
            if (f.unit_name) {
                measureSelect.value = 'unit';
                document.getElementById('custom-unit-name').textContent = f.unit_name;
                if (f.g_per_unit) {
                    document.getElementById('custom-weight').value = f.g_per_unit;
                }
            } else {
                measureSelect.value = 'g';
            }
            measureSelect.dispatchEvent(new Event('change'));
        }
        
        if (measureSelect && measureSelect.value !== 'g' && (qtyInput.value == "" || qtyInput.value == "100")) {
            qtyInput.value = "1";
        }
        
        updatePreview();
      });
      foodDropdown.appendChild(item);
    });
    foodDropdown.style.display = 'block';
  });

  document.addEventListener('click', e => {
    if (!foodSearchInput.contains(e.target) && !foodDropdown.contains(e.target)) {
      foodDropdown.style.display = 'none';
    }
  });
}

// ... (seletor de medida permanece igual)

function updatePreview() {
  if (!window.selectedFood || !qtyInput) return;
  
  const measure = document.getElementById('measure-select').value;
  let qty = parseFloat(qtyInput.value) || 0;
  let displayQty = qty;
  let unitLabel = 'g';

  if (measure !== 'g') {
    const weightPerUnit = parseFloat(document.getElementById('custom-weight').value) || 0;
    qty = qty * weightPerUnit; 
    unitLabel = document.getElementById('measure-select').options[document.getElementById('measure-select').selectedIndex].text;
  }

  const f = qty / 100;
  const kcal = (window.selectedFood.kcal * f).toFixed(1);
  const prot = (window.selectedFood.prot * f).toFixed(1);
  const carb = (window.selectedFood.carb * f).toFixed(1);
  const fat = (window.selectedFood.fat * f).toFixed(1);
  
  if (previewDiv) {
    let html = '';
    if (measure !== 'g') {
       const weightPerUnit = parseFloat(document.getElementById('custom-weight').value) || 0;
       if (weightPerUnit <= 0) {
          previewDiv.innerHTML = `<div class="alert alert-warning" style="margin-top:10px;">⚠ Informe o peso de 1 ${unitLabel.toLowerCase()} para calcular.</div>`;
          return;
       }
    }

    html = `
        <div style="background:rgba(255,255,255,0.03); padding:16px; border-radius:12px; border:1px solid var(--border); margin-top:15px; animation: slideIn 0.3s ease;">
            <div style="font-size:0.8rem; color:var(--dim); margin-bottom:10px; display:flex; justify-content:space-between;">
                <span>PRÉVIA NUTRICIONAL</span>
                <span>${qty.toFixed(0)}g total</span>
            </div>
            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; text-align:center;">
                <div>
                    <div style="font-size:1.1rem; font-weight:800; color:var(--yellow);">${kcal}</div>
                    <div style="font-size:0.65rem; color:var(--dim);">KCAL</div>
                </div>
                <div>
                    <div style="font-size:1.1rem; font-weight:800; color:var(--prot);">${prot}g</div>
                    <div style="font-size:0.65rem; color:var(--dim);">PROT</div>
                </div>
                <div>
                    <div style="font-size:1.1rem; font-weight:800; color:var(--carb);">${carb}g</div>
                    <div style="font-size:0.65rem; color:var(--dim);">CARB</div>
                </div>
                <div>
                    <div style="font-size:1.1rem; font-weight:800; color:var(--fat);">${fat}g</div>
                    <div style="font-size:0.65rem; color:var(--dim);">GORD</div>
                </div>
            </div>
        </div>`;
    
    previewDiv.innerHTML = html;
    previewDiv.style.display = 'block';
  }
}


// ─── BMR Portion Calculator ───────────────────────────────────────────────────
const bmrCalcBtn = document.getElementById('portion-calc-btn');
if (bmrCalcBtn) {
  bmrCalcBtn.addEventListener('click', () => {
    const kcal100 = parseFloat(document.getElementById('p-kcal100').value) || 0;
    const prot100 = parseFloat(document.getElementById('p-prot100').value) || 0;
    const qty = parseFloat(document.getElementById('p-qty').value) || 0;
    const targetKcal = parseFloat(document.getElementById('p-target').value) || 0;
    const resultEl = document.getElementById('portion-result');

    let msg = '';
    if (qty && kcal100) {
      const kcal = (kcal100 * qty / 100).toFixed(1);
      const prot = (prot100 * qty / 100).toFixed(1);
      msg += `✅ ${qty}g → ${kcal} kcal | ${prot}g prot.`;
    }
    if (targetKcal && kcal100) {
      const grams = ((targetKcal / kcal100) * 100).toFixed(1);
      msg += (msg ? '   |   ' : '') + `✅ ${targetKcal} kcal → ${grams}g`;
    }
    if (!msg) msg = '⚠ Preencha os campos acima.';
    resultEl.textContent = msg;
  });
}

// ─── AJAX Deletion (meals page) ────────────────────────────────────────────────
document.addEventListener('submit', async e => {
  if (e.target.classList.contains('ajax-delete-form')) {
    e.preventDefault();
    if (!confirm('Remover este item?')) return;

    const form = e.target;
    const itemRow = form.closest('.meal-item');
    if (!itemRow) return;

    try {
      const res = await fetch(form.action, {
        method: 'POST',
        headers: { 'Accept': 'application/json' }
      });
      const data = await res.json();

      if (data.success) {
        // 1. Extrair valores do item removido
        const itemKcal = parseFloat(itemRow.dataset.kcal) || 0;
        const itemProt = parseFloat(itemRow.dataset.prot) || 0;
        const itemCarb = parseFloat(itemRow.dataset.carb) || 0;
        const itemFat = parseFloat(itemRow.dataset.fat) || 0;
        const mealType = itemRow.dataset.meal;

        // 2. Atualizar Totais do Dia
        const updateVal = (id, subtract) => {
            const el = document.getElementById(id);
            if (el) {
                const current = parseFloat(el.textContent) || 0;
                el.textContent = Math.max(0, current - subtract).toFixed(1);
                return parseFloat(el.textContent);
            }
            return 0;
        };
        
        const newTotalKcal = updateVal('total-kcal-val', itemKcal);
        const newTotalProt = updateVal('total-prot-val', itemProt);
        const newTotalCarb = updateVal('total-carb-val', itemCarb);
        const newTotalFat = updateVal('total-fat-val', itemFat);

        // 3. Atualizar Barra de Progresso Principal (Kcal)
        const goalKcal = parseFloat(document.getElementById('goal-kcal-val')?.textContent) || 2000;
        const pct = Math.min(100, Math.floor((newTotalKcal / goalKcal) * 100));
        const progressFill = document.getElementById('progress-bar-fill');
        const progressPct = document.getElementById('progress-percent');
        if (progressFill) {
            progressFill.style.width = pct + '%';
            progressFill.dataset.width = pct;
            if (pct >= 100) progressFill.classList.add('over');
            else progressFill.classList.remove('over');
        }
        if (progressPct) progressPct.textContent = pct;

        // 4. Atualizar Barras de Macros Secundárias
        const updateBar = (idSuffix, currentVal, goalId) => {
            const fill = document.getElementById('total-' + idSuffix + '-fill');
            const goal = parseFloat(document.getElementById(goalId)?.textContent) || 100;
            if (fill) {
                const pctMacro = Math.min(100, Math.floor((currentVal / goal) * 100));
                fill.style.width = pctMacro + '%';
                fill.dataset.width = pctMacro;
            }
        };
        updateBar('prot', newTotalProt, 'goal-prot-val');
        updateBar('carb', newTotalCarb, 'goal-carb-val');
        updateBar('fat', newTotalFat, 'goal-fat-val');

        // 5. Remover o elemento com animação

        itemRow.style.transition = 'all 0.3s ease';
        itemRow.style.opacity = '0';
        itemRow.style.transform = 'translateX(20px)';
        setTimeout(() => {
            const parent = itemRow.parentElement;
            itemRow.remove();
            // Se a refeição ficou vazia, poderíamos remover o card inteiro, mas manter é mais simples
        }, 300);

      } else {
        alert('Erro ao remover item.');
      }
    } catch (err) {
      console.error(err);
      alert('Erro de conexão.');
    }
  }
});

// ─── Confirm delete (generic) ─────────────────────────────────────────────────

// ─── Progress bar animation ───────────────────────────────────────────────────
document.querySelectorAll('.progress-fill').forEach(bar => {
  const target = bar.dataset.width || '0';
  bar.style.width = '0%';
  setTimeout(() => { bar.style.width = target + '%'; }, 100);
});
