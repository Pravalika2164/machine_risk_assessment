
let fields = [];
let machines = [];
let editing = null;
let editingFieldId = null;
let risks = {};

const CORE_FIELDS = new Set([
  'machine_name',
  'temperature',
  'pressure',
  'vibration'
]);

const $ = id => document.getElementById(id);

function notice(message) {
  const toast = $('toast');
  toast.textContent = message;
  toast.style.display = 'block';

  clearTimeout(notice.timer);
  notice.timer = setTimeout(() => {
    toast.style.display = 'none';
  }, 5000);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }

  return data;
}

function element(tag, text, className) {
  const node = document.createElement(tag);

  if (text !== undefined) {
    node.textContent = text;
  }

  if (className) {
    node.className = className;
  }

  return node;
}

// ---------------------------------------
// 1. RENDER CONFIGURED FIELDS
// ---------------------------------------

function renderFields() {
  const list = $('fieldList');
  list.replaceChildren();

  fields.forEach(field => {
    const item = element('div', undefined, 'field-item');

    const description = element(
      'span',
      `${field.label} · ${field.type}${field.required ? ' · Required' : ' · Optional'}`,
      'chip'
    );

    item.append(description);

    if (!CORE_FIELDS.has(field.name)) {
      const editButton = element('button', 'Edit', 'secondary');
      editButton.type = 'button';
      editButton.onclick = () => editField(field);

      const deleteButton = element('button', 'Delete', 'secondary');
      deleteButton.type = 'button';
      deleteButton.onclick = () => deleteField(field);

      item.append(editButton, deleteButton);
    }

    list.append(item);
  });

  $('fieldCount').textContent = fields.length;

  const container = $('dynamicInputs');

  // Preserve unsaved values when field configuration refreshes.
  const previousValues = {};

  container.querySelectorAll('[name]').forEach(input => {
    previousValues[input.name] = input.value;
  });

  container.replaceChildren();

  fields.forEach(field => {
    const label = element(
      'label',
      field.label + (field.required ? ' *' : '')
    );

    let input;

    if (field.type === 'dropdown') {
      input = document.createElement('select');
      input.append(new Option('Select ' + field.label, ''));

      (field.options || []).forEach(option => {
        input.append(new Option(option, option));
      });
    } else {
      input = document.createElement('input');
      input.type = field.type === 'number' ? 'number' : 'text';

      if (field.type === 'number') {
        input.step = 'any';
      }
    }

    input.name = field.name;
    input.required = Boolean(field.required);

    if (Object.prototype.hasOwnProperty.call(previousValues, field.name)) {
      input.value = previousValues[field.name];
    }

    label.append(input);
    container.append(label);
  });
}

// ---------------------------------------
// 2. FIELD EDITING DIALOG
// ---------------------------------------

function editField(field) {
  editingFieldId = field.id;

  $('editFieldLabel').value = field.label;
  $('editFieldType').value = field.type;
  $('editFieldRequired').checked = Boolean(field.required);
  $('editFieldOptions').value = (field.options || []).join(', ');

  updateEditOptionsVisibility();
  $('editFieldDialog').showModal();
}

function updateEditOptionsVisibility() {
  $('editOptionsWrap').hidden =
    $('editFieldType').value !== 'dropdown';
}

$('editFieldType').addEventListener(
  'change',
  updateEditOptionsVisibility
);

$('cancelFieldEdit').onclick = () => {
  $('editFieldDialog').close();
};

$('editFieldDialog').addEventListener('close', () => {
  editingFieldId = null;
});

$('editFieldForm').onsubmit = async event => {
  event.preventDefault();

  if (editingFieldId === null) return;

  const type = $('editFieldType').value;

  const options = type === 'dropdown'
    ? $('editFieldOptions').value
        .split(',')
        .map(value => value.trim())
        .filter(Boolean)
    : [];

  const payload = {
    label: $('editFieldLabel').value.trim(),
    type,
    required: $('editFieldRequired').checked,
    options
  };

  try {
    await api(`/api/fields/${editingFieldId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });

    $('editFieldDialog').close();
    await refresh();

    notice('Field updated successfully');
  } catch (error) {
    notice(error.message);
  }
};

// ---------------------------------------
// 3. DELETE CUSTOM FIELD
// ---------------------------------------

async function deleteField(field) {
  if (CORE_FIELDS.has(field.name)) {
    notice('Core fields cannot be deleted');
    return;
  }

  const confirmed = confirm(
    `Delete "${field.label}"?\n\n` +
    'This will permanently remove this field and its values ' +
    'from all existing machine records.'
  );

  if (!confirmed) return;

  try {
    await api(`/api/fields/${field.id}`, {
      method: 'DELETE'
    });

    await refresh();
    notice('Field deleted successfully');
  } catch (error) {
    notice(error.message);
  }
}

// ---------------------------------------
// 4. ADD NEW FIELD
// ---------------------------------------

$('fieldType').onchange = () => {
  $('optionsWrap').hidden =
    $('fieldType').value !== 'dropdown';
};

$('fieldForm').onsubmit = async event => {
  event.preventDefault();

  const type = $('fieldType').value;

  const payload = {
    label: $('fieldName').value.trim(),
    type,
    required: $('fieldRequired').checked,
    options: type === 'dropdown'
      ? $('fieldOptions').value
          .split(',')
          .map(value => value.trim())
          .filter(Boolean)
      : []
  };

  try {
    await api('/api/fields', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    $('fieldForm').reset();
    $('optionsWrap').hidden = true;

    await refresh();
    notice('Field added successfully');
  } catch (error) {
    notice(error.message);
  }
};

// ---------------------------------------
// 5. RENDER MACHINE RECORDS
// ---------------------------------------

function renderMachines() {
  const rows = $('machineRows');
  rows.replaceChildren();

  $('machineCount').textContent = machines.length;

  if (!machines.length) {
    const row = document.createElement('tr');
    const cell = element(
      'td',
      'No machines yet. Add your first machine.'
    );

    cell.colSpan = 6;
    row.append(cell);
    rows.append(row);
    return;
  }

  machines.forEach((machine, index) => {
    const row = document.createElement('tr');

    row.append(
        element('td', String(index + 1)),
        element('td', String(machine.id)),
        element('td', String(machine.data.machine_name || 'Unnamed'))
    );

    const attributes = Object.entries(machine.data)
      .filter(([key]) => key !== 'machine_name')
      .map(([key, value]) => {
        const field = fields.find(item => item.name === key);
        const label = field?.label || key;
        return `${label}: ${value}`;
      })
      .join(' · ');

    row.append(element('td', attributes || '—'));

    const riskCell = document.createElement('td');
    const risk = risks[machine.id];

    if (risk) {
      riskCell.append(
        element(
          'span',
          risk,
          `risk ${risk.split(' ')[0].toLowerCase()}`
        )
      );
    } else {
      riskCell.textContent = 'Not predicted';
    }

    row.append(riskCell);

    const actions = document.createElement('td');
    actions.className = 'row-actions';

    const buttons = [
      ['Predict', () => runPrediction(machine.id), ''],
      ['Edit', () => editMachine(machine), 'secondary'],
      ['Delete', () => deleteMachine(machine.id), 'secondary']
    ];

    buttons.forEach(([label, callback, className]) => {
      const button = element('button', label, className);
      button.type = 'button';
      button.onclick = callback;
      actions.append(button);
    });

    row.append(actions);
    rows.append(row);
  });
}

// ---------------------------------------
// 6. LOAD FIELDS AND MACHINES
// ---------------------------------------

async function refresh() {
  const [newFields, newMachines] = await Promise.all([
    api('/api/fields'),
    api('/api/machines')
  ]);

  fields = newFields;
  machines = newMachines;

  // Predictions are not persisted by the current backend.
  // Clear cached results when machine records change.
  risks = {};

  renderFields();
  renderMachines();
}

// ---------------------------------------
// 7. MACHINE CREATE / UPDATE
// ---------------------------------------

function resetEditor() {
  editing = null;
  $('machineForm').reset();
  $('saveMachine').textContent = 'Save machine';
}

$('resetForm').onclick = resetEditor;

$('machineForm').onsubmit = async event => {
  event.preventDefault();

  const data = {};

  new FormData(event.target).forEach((value, key) => {
    if (value !== '') {
      data[key] = value;
    }
  });

  try {
    const isEditing = editing !== null;

    await api(
      isEditing
        ? `/api/machines/${editing}`
        : '/api/machines',
      {
        method: isEditing ? 'PUT' : 'POST',
        body: JSON.stringify(data)
      }
    );

    resetEditor();
    await refresh();
    notice('Machine saved successfully');
  } catch (error) {
    notice(error.message);
  }
};

function editMachine(machine) {
  editing = machine.id;

  $('machineForm').reset();

  for (const input of $('machineForm').elements) {
    if (input.name) {
      input.value = machine.data[input.name] ?? '';
    }
  }

  $('saveMachine').textContent = 'Update machine';

  $('machineForm').scrollIntoView({
    behavior: 'smooth',
    block: 'start'
  });
}

// ---------------------------------------
// 8. DELETE MACHINE
// ---------------------------------------

async function deleteMachine(id) {
  if (!confirm('Are you sure you want to delete this machine?')) {
    return;
  }

  try {
    await api(`/api/machines/${id}`, {
      method: 'DELETE'
    });

    if (editing === id) {
      resetEditor();
    }

    delete risks[id];
    await refresh();

    notice('Machine deleted successfully');
  } catch (error) {
    notice(error.message);
  }
}

// ---------------------------------------
// 9. PREDICT MACHINE RISK
// ---------------------------------------

async function runPrediction(id) {
  try {
    const result = await api(`/api/predict/${id}`, {
      method: 'POST'
    });

    risks[id] = result.risk;

    renderMachines();
    notice(`Machine ${id}: ${result.risk}`);
  } catch (error) {
    notice(error.message);
  }
}

// ---------------------------------------
// 10. INITIAL LOAD
// ---------------------------------------

refresh().catch(error => notice(error.message));
