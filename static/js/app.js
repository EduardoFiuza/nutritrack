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
        <span class="di-stats">${f.kcal} <small>kcal/100g</small> | ${f.prot}g <small>prot</small></span>`;
      item.addEventListener('click', () => {
        window.selectedFood = f;
        foodSearchInput.value = f.name;
        foodIdInput.value = f.id;
        foodDropdown.style.display = 'none';
        
        // Sugerir a unidade caso o alimento tenha uma pré-definida
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
        
        // Se a quantidade estiver vazia ou for 100 (padrão antigo), mudar para 1 se for unidade
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

// Escutar mudanças no seletor de medida (Grama vs Unidade/Fatia/etc)
const measureSelect = document.getElementById('measure-select');
if (measureSelect) {
    measureSelect.addEventListener('change', () => {
        const val = measureSelect.value;
        const weightWrap = document.getElementById('custom-weight-wrap');
        const unitLabel = document.getElementById('custom-unit-name');
        
        if (val === 'g') {
            weightWrap.style.display = 'none';
            if (qtyInput.value == "1") qtyInput.value = "100";
        } else {
            weightWrap.style.display = 'block';
            unitLabel.textContent = measureSelect.options[measureSelect.selectedIndex].text.toLowerCase();
            if (qtyInput.value == "100") qtyInput.value = "1";
        }
        updatePreview();
    });
}

const customWeightInput = document.getElementById('custom-weight');
if (customWeightInput) {
    customWeightInput.addEventListener('input', updatePreview);
}

if (qtyInput) {
  qtyInput.addEventListener('input', updatePreview);
}

function updatePreview() {
  if (!window.selectedFood || !qtyInput) return;
  
  const measure = document.getElementById('measure-select').value;
  let qty = parseFloat(qtyInput.value) || 0;
  let displayQty = qty;
  let unitLabel = 'g';

  if (measure !== 'g') {
    const weightPerUnit = parseFloat(document.getElementById('custom-weight').value) || 0;
    qty = qty * weightPerUnit; // Converte para gramas para o cálculo
    unitLabel = document.getElementById('measure-select').options[document.getElementById('measure-select').selectedIndex].text;
  }

  const kcal = (window.selectedFood.kcal * qty / 100).toFixed(1);
  const prot = (window.selectedFood.prot * qty / 100).toFixed(1);
  
  if (previewDiv) {
    if (measure !== 'g') {
       const weightPerUnit = parseFloat(document.getElementById('custom-weight').value) || 0;
       if (weightPerUnit > 0) {
          previewDiv.innerHTML = `
            <div style="background:rgba(67,233,123,0.1); padding:10px; border-radius:8px; border:1px solid var(--green); margin-top:10px;">
                <div style="font-size:0.8rem; color:var(--dim); margin-bottom:4px;">Resultado do cálculo:</div>
                <div style="font-size:1.1rem; font-weight:700; color:var(--green);">
                    🔥 ${kcal} kcal | 💪 ${prot}g prot.
                </div>
                <div style="font-size:0.75rem; color:var(--dim); margin-top:2px;">
                    Considerando ${displayQty} ${unitLabel.toLowerCase()} (${qty.toFixed(0)}g total)
                </div>
            </div>`;
       } else {
          previewDiv.textContent = `⚠ Informe o peso de 1 ${unitLabel.toLowerCase()} para ver as calorias.`;
       }
    } else {
        previewDiv.innerHTML = `
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; border:1px solid var(--border); margin-top:10px;">
                <div style="font-size:1.1rem; font-weight:700; color:var(--yellow);">
                    🔥 ${kcal} kcal | 💪 ${prot}g prot.
                </div>
                <div style="font-size:0.75rem; color:var(--dim);">${qty}g de ${window.selectedFood.name}</div>
            </div>`;
    }
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
        const mealType = itemRow.dataset.meal;

        // 2. Atualizar Totais do Dia
        const totalKcalEl = document.getElementById('total-kcal-val');
        const totalProtEl = document.getElementById('total-prot-val');
        const currentTotalKcal = parseFloat(totalKcalEl.textContent) || 0;
        const currentTotalProt = parseFloat(totalProtEl.textContent) || 0;
        
        const newTotalKcal = Math.max(0, currentTotalKcal - itemKcal);
        const newTotalProt = Math.max(0, currentTotalProt - itemProt);
        
        totalKcalEl.textContent = newTotalKcal.toFixed(1);
        totalProtEl.textContent = newTotalProt.toFixed(1);

        // 3. Atualizar Totais da Refeição
        const mealKcalEl = document.querySelector(`.meal-kcal-val[data-meal="${mealType}"]`);
        const mealProtEl = document.querySelector(`.meal-prot-val[data-meal="${mealType}"]`);
        if (mealKcalEl && mealProtEl) {
           const currentMealKcal = parseFloat(mealKcalEl.textContent) || 0;
           const currentMealProt = parseFloat(mealProtEl.textContent) || 0;
           mealKcalEl.textContent = Math.max(0, currentMealKcal - itemKcal).toFixed(1);
           mealProtEl.textContent = Math.max(0, currentMealProt - itemProt).toFixed(1);
        }

        // 4. Atualizar Barra de Progresso
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
