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
        <span class="di-stats">${f.kcal} kcal | ${f.prot}g prot</span>`;
      item.addEventListener('click', () => {
        selectedFood = f;
        foodSearchInput.value = f.name;
        foodIdInput.value = f.id;
        foodDropdown.style.display = 'none';
        
        // Se tem unidade, mostra o seletor de modo
        const unitWrap = document.getElementById('unit-mode-wrap');
        if (unitWrap) {
           if (f.unit_name) {
               unitWrap.style.display = 'flex';
               document.getElementById('unit-name-label').textContent = f.unit_name;
           } else {
               unitWrap.style.display = 'none';
               document.getElementById('mode-grams').checked = true;
           }
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

// Escutar mudanças no modo (Gramas vs Unidade)
document.querySelectorAll('input[name="qty_mode"]').forEach(radio => {
  radio.addEventListener('change', updatePreview);
});

if (qtyInput) {
  qtyInput.addEventListener('input', updatePreview);
}

function updatePreview() {
  if (!selectedFood || !qtyInput) return;
  
  const mode = document.querySelector('input[name="qty_mode"]:checked')?.value || 'g';
  let qty = parseFloat(qtyInput.value) || 0;
  let displayQty = qty;
  let unitLabel = 'g';

  if (mode === 'unit' && selectedFood.g_per_unit) {
    qty = qty * selectedFood.g_per_unit; // Converte para gramas para o cálculo
    unitLabel = selectedFood.unit_name;
  }

  const kcal = (selectedFood.kcal * qty / 100).toFixed(1);
  const prot = (selectedFood.prot * qty / 100).toFixed(1);
  
  if (previewDiv) {
    if (mode === 'unit') {
        previewDiv.textContent = `➡ ${displayQty} ${unitLabel} (${qty.toFixed(0)}g) → 🔥 ${kcal} kcal | 💪 ${prot}g prot.`;
    } else {
        previewDiv.textContent = `➡ ${qty}g de ${selectedFood.name} → 🔥 ${kcal} kcal | 💪 ${prot}g prot.`;
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

// ─── Confirm delete ───────────────────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// ─── Progress bar animation ───────────────────────────────────────────────────
document.querySelectorAll('.progress-fill').forEach(bar => {
  const target = bar.dataset.width || '0';
  bar.style.width = '0%';
  setTimeout(() => { bar.style.width = target + '%'; }, 100);
});
