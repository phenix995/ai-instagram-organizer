const settingsForm = document.getElementById('settings-form');
const statusIndicator = document.getElementById('status-indicator');
const statusLabel = document.getElementById('status-label');
const commandDisplay = document.getElementById('command-display');
const startButton = document.getElementById('start-btn');
const stopButton = document.getElementById('stop-btn');
const logOutput = document.getElementById('log-output');
const clearLogButton = document.getElementById('clear-log');
const imageGrid = document.getElementById('image-grid');
const imageFolderBadge = document.getElementById('image-folder');
const imageError = document.getElementById('image-error');

let cliArguments = [];
let defaultValues = {};
let pollingInterval = null;

const debounce = (fn, delay = 400) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
};

const titleCase = (value) =>
  value
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());

const determineStep = (type) => (type === 'float' ? '0.1' : '1');

const resolveDefaultValue = (arg) => {
  const override = defaultValues[arg.dest];
  if (override !== undefined && override !== null) {
    return override;
  }
  if (arg.default !== undefined && arg.default !== null) {
    return arg.default;
  }
  if (arg.type === 'boolean') {
    return false;
  }
  return '';
};

const createField = (arg) => {
  const wrapper = document.createElement('div');
  wrapper.className = 'rounded-2xl border border-slate-700/40 bg-slate-900/30 p-5 space-y-3 shadow-inner shadow-slate-900/40';

  const headerRow = document.createElement('div');
  headerRow.className = 'flex items-center justify-between gap-4';

  const label = document.createElement('label');
  label.className = 'text-sm font-semibold text-slate-100 tracking-wide';
  label.htmlFor = `arg-${arg.dest}`;
  label.textContent = titleCase(arg.dest);
  headerRow.appendChild(label);

  let inputElement;

  if (arg.type === 'boolean') {
    const toggleLabel = document.createElement('label');
    toggleLabel.className = 'toggle-switch';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `arg-${arg.dest}`;
    checkbox.dataset.arg = arg.dest;
    checkbox.dataset.type = arg.type;
    checkbox.checked = Boolean(resolveDefaultValue(arg));
    const slider = document.createElement('span');
    slider.className = 'toggle-slider';
    toggleLabel.appendChild(checkbox);
    toggleLabel.appendChild(slider);
    headerRow.appendChild(toggleLabel);
    inputElement = checkbox;
  } else if (arg.choices && Array.isArray(arg.choices)) {
    const select = document.createElement('select');
    select.id = `arg-${arg.dest}`;
    select.dataset.arg = arg.dest;
    select.dataset.type = arg.type;
    select.className = 'w-full rounded-xl border px-4 py-2.5 text-sm focus:outline-none transition';
    const placeholderOption = document.createElement('option');
    placeholderOption.value = '';
    placeholderOption.textContent = 'Select…';
    select.appendChild(placeholderOption);
    arg.choices.forEach((choice) => {
      const option = document.createElement('option');
      option.value = choice;
      option.textContent = choice;
      select.appendChild(option);
    });
    const defaultValue = resolveDefaultValue(arg);
    if (defaultValue !== '') {
      select.value = defaultValue;
    }
    inputElement = select;
  } else {
    const input = document.createElement('input');
    input.id = `arg-${arg.dest}`;
    input.dataset.arg = arg.dest;
    input.dataset.type = arg.type;
    input.className = 'w-full rounded-xl border px-4 py-2.5 text-sm focus:outline-none transition';
    input.placeholder = `Enter ${titleCase(arg.dest)}`;
    if (arg.type === 'integer' || arg.type === 'float') {
      input.type = 'number';
      input.step = determineStep(arg.type);
    } else {
      input.type = 'text';
    }
    const defaultValue = resolveDefaultValue(arg);
    if (defaultValue !== undefined && defaultValue !== null && defaultValue !== '') {
      input.value = defaultValue;
    }
    inputElement = input;
  }

  wrapper.appendChild(headerRow);

  if (inputElement && arg.type !== 'boolean') {
    wrapper.appendChild(inputElement);
  }

  const helpText = document.createElement('p');
  helpText.className = 'text-xs text-slate-400 leading-relaxed';
  helpText.textContent = arg.help || 'No description provided for this setting.';
  wrapper.appendChild(helpText);

  return { wrapper, inputElement };
};

const LLM_ARGUMENT_KEYS = new Set([
  'ai_provider',
  'llama_key',
  'gemini_key',
  'ollama_url',
  'ollama_model',
]);

const createLlmInput = (arg, { label, placeholder, type = 'text' }) => {
  const container = document.createElement('div');
  container.className = 'space-y-2';

  const fieldLabel = document.createElement('label');
  fieldLabel.className = 'text-xs uppercase tracking-[0.3em] text-slate-400';
  fieldLabel.htmlFor = `arg-${arg.dest}`;
  fieldLabel.textContent = label;

  const input = document.createElement('input');
  input.id = `arg-${arg.dest}`;
  input.dataset.arg = arg.dest;
  input.dataset.type = arg.type;
  input.className = 'w-full rounded-xl border px-4 py-2.5 text-sm focus:outline-none transition';
  input.placeholder = placeholder;
  input.type = type;

  const defaultValue = resolveDefaultValue(arg);
  if (defaultValue !== undefined && defaultValue !== null && defaultValue !== '') {
    input.value = defaultValue;
  }

  container.appendChild(fieldLabel);
  container.appendChild(input);

  return { container, input };
};

const createLlmSection = (llmArgs) => {
  const providerArg = llmArgs.ai_provider;
  if (!providerArg) {
    return null;
  }

  const wrapper = document.createElement('div');
  wrapper.className = 'rounded-2xl border border-slate-700/40 bg-slate-900/30 p-5 space-y-4 shadow-inner shadow-slate-900/40';

  const headerRow = document.createElement('div');
  headerRow.className = 'flex flex-col gap-2';

  const title = document.createElement('span');
  title.className = 'text-sm font-semibold text-slate-100 tracking-wide';
  title.textContent = 'LLM Provider';

  const description = document.createElement('p');
  description.className = 'text-xs text-slate-400 leading-relaxed';
  description.textContent = 'Choose which large language model to use and provide the required connection details.';

  headerRow.appendChild(title);
  headerRow.appendChild(description);

  const select = document.createElement('select');
  select.id = `arg-${providerArg.dest}`;
  select.dataset.arg = providerArg.dest;
  select.dataset.type = providerArg.type;
  select.className = 'w-full rounded-xl border px-4 py-2.5 text-sm focus:outline-none transition';

  const placeholderOption = document.createElement('option');
  placeholderOption.value = '';
  placeholderOption.textContent = 'Select a provider…';
  select.appendChild(placeholderOption);

  (providerArg.choices || []).forEach((choice) => {
    const option = document.createElement('option');
    option.value = choice;
    option.textContent = titleCase(choice);
    select.appendChild(option);
  });

  const defaults = resolveDefaultValue(providerArg);
  if (defaults !== '') {
    select.value = defaults;
  }

  const fieldContainer = document.createElement('div');
  fieldContainer.className = 'space-y-4';

  const providerDescriptions = {
    llama: 'Use the official Llama API. Provide your API key to authenticate requests.',
    gemini: 'Connect to Google Gemini services with your API key.',
    ollama: 'Connect to a self-hosted Ollama endpoint by specifying the base URL and model.',
  };

  const activeDescription = document.createElement('p');
  activeDescription.className = 'text-xs text-slate-300 leading-relaxed hidden';

  const providers = {};

  if (llmArgs.llama_key) {
    const llamaInput = createLlmInput(llmArgs.llama_key, {
      label: 'Llama API Key',
      placeholder: 'Enter your Llama API key',
    });
    providers.llama = [llamaInput];
    fieldContainer.appendChild(llamaInput.container);
  }

  if (llmArgs.gemini_key) {
    const geminiInput = createLlmInput(llmArgs.gemini_key, {
      label: 'Gemini API Key',
      placeholder: 'Enter your Gemini API key',
    });
    providers.gemini = [geminiInput];
    fieldContainer.appendChild(geminiInput.container);
  }

  const ollamaInputs = [];
  if (llmArgs.ollama_url) {
    ollamaInputs.push(
      createLlmInput(llmArgs.ollama_url, {
        label: 'Ollama API URL',
        placeholder: 'http://localhost:11434/api/generate',
      })
    );
  }
  if (llmArgs.ollama_model) {
    ollamaInputs.push(
      createLlmInput(llmArgs.ollama_model, {
        label: 'Ollama Model Name',
        placeholder: 'Enter the model to request (e.g., gemma3:4b)',
      })
    );
  }
  if (ollamaInputs.length) {
    providers.ollama = ollamaInputs;
    ollamaInputs.forEach((input) => fieldContainer.appendChild(input.container));
  }

  const setActiveProvider = (provider) => {
    Object.entries(providers).forEach(([name, inputs]) => {
      const isActive = name === provider;
      inputs.forEach(({ container, input }) => {
        container.classList.toggle('hidden', !isActive);
        input.disabled = !isActive;
      });
    });

    if (provider && providerDescriptions[provider]) {
      activeDescription.textContent = providerDescriptions[provider];
      activeDescription.classList.remove('hidden');
    } else {
      activeDescription.textContent = '';
      activeDescription.classList.add('hidden');
    }
  };

  select.addEventListener('change', () => setActiveProvider(select.value));

  wrapper.appendChild(headerRow);
  wrapper.appendChild(select);
  wrapper.appendChild(activeDescription);
  wrapper.appendChild(fieldContainer);

  const initialProvider = select.value || '';
  setActiveProvider(initialProvider);

  return { wrapper, select };
};

const buildForm = () => {
  settingsForm.innerHTML = '';
  let initialSource = null;

  const llmArgs = {};
  const pendingWrappers = [];

  cliArguments.forEach((arg) => {
    if (LLM_ARGUMENT_KEYS.has(arg.dest)) {
      llmArgs[arg.dest] = arg;
      return;
    }

    const { wrapper, inputElement } = createField(arg);
    pendingWrappers.push(wrapper);

    if (inputElement && arg.dest === 'source') {
      const updateImages = debounce(() => updateImageViewer(inputElement.value));
      inputElement.addEventListener('input', updateImages);
      if (initialSource === null) {
        initialSource = inputElement.value;
      }
    }
  });

  const llmSection = createLlmSection(llmArgs);
  if (llmSection) {
    settingsForm.appendChild(llmSection.wrapper);
  }

  pendingWrappers.forEach((wrapper) => settingsForm.appendChild(wrapper));

  if (initialSource) {
    updateImageViewer(initialSource);
  } else {
    updateImageViewer('');
  }
};

const collectSettings = () => {
  const settings = {};
  document.querySelectorAll('[data-arg]').forEach((element) => {
    if (element.disabled) {
      return;
    }

    const name = element.dataset.arg;
    const type = element.dataset.type;

    if (element.type === 'checkbox') {
      settings[name] = element.checked;
      return;
    }

    if (element.value === undefined || element.value === null) {
      return;
    }

    const value = element.value.toString().trim();
    if (value === '') {
      return;
    }

    if (type === 'integer') {
      settings[name] = parseInt(value, 10);
    } else if (type === 'float') {
      settings[name] = parseFloat(value);
    } else {
      settings[name] = value;
    }
  });
  return settings;
};

const updateStatusUI = ({ running, exit_code: exitCode, command }) => {
  statusIndicator.classList.remove('idle', 'running', 'error');
  let label = 'IDLE';

  if (running) {
    statusIndicator.classList.add('running');
    label = 'RUNNING';
  } else if (exitCode === null || exitCode === undefined) {
    statusIndicator.classList.add('idle');
    label = 'IDLE';
  } else if (exitCode === 0) {
    statusIndicator.classList.add('running');
    label = 'COMPLETED';
  } else {
    statusIndicator.classList.add('error');
    label = 'FAILED';
  }

  statusLabel.textContent = label;

  if (command && command.length > 0) {
    commandDisplay.textContent = command.join(' ');
  } else {
    commandDisplay.textContent = 'Waiting for launch configuration…';
  }

  startButton.disabled = running;
  startButton.classList.toggle('opacity-60', running);
  stopButton.disabled = !running;
  stopButton.classList.toggle('opacity-60', !running);
};

const renderLogs = (logs) => {
  logOutput.textContent = logs.join('\n');
  logOutput.scrollTop = logOutput.scrollHeight;
};

const updateImageViewer = async (folder) => {
  if (!folder) {
    imageFolderBadge.textContent = 'source: —';
    imageGrid.innerHTML = '';
    imageError.classList.add('hidden');
    return;
  }

  imageFolderBadge.textContent = `source: ${folder}`;

  try {
    const response = await fetch(`/api/images?folder=${encodeURIComponent(folder)}`);
    const payload = await response.json();

    imageGrid.innerHTML = '';

    if (!response.ok || payload.error) {
      imageError.textContent = payload.error || 'Unable to load images';
      imageError.classList.remove('hidden');
      return;
    }

    imageError.classList.add('hidden');

    payload.images.forEach((image) => {
      const card = document.createElement('div');
      card.className = 'image-card';
      const img = document.createElement('img');
      img.src = image.data;
      img.alt = image.name;
      img.loading = 'lazy';
      card.appendChild(img);
      const caption = document.createElement('div');
      caption.className = 'p-3 text-xs text-slate-300 truncate';
      caption.textContent = image.name;
      card.appendChild(caption);
      imageGrid.appendChild(card);
    });
  } catch (error) {
    imageError.textContent = 'Unable to load images';
    imageError.classList.remove('hidden');
  }
};

const fetchStatus = async () => {
  try {
    const response = await fetch('/api/status');
    const payload = await response.json();
    updateStatusUI(payload);
    renderLogs(payload.logs || []);
  } catch (error) {
    console.error('Failed to fetch status', error);
  }
};

const startProcess = async () => {
  const settings = collectSettings();

  try {
    const response = await fetch('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings }),
    });

    if (!response.ok) {
      const payload = await response.json();
      commandDisplay.textContent = `Error: ${payload.detail || 'Unable to start process'}`;
      return;
    }

    const payload = await response.json();
    updateStatusUI({ running: true, exit_code: null, command: payload.command });
  } catch (error) {
    commandDisplay.textContent = `Error: ${error.message}`;
  } finally {
    fetchStatus();
  }
};

const stopProcess = async () => {
  try {
    await fetch('/api/stop', { method: 'POST' });
  } catch (error) {
    console.error('Unable to stop process', error);
  } finally {
    fetchStatus();
  }
};

const clearLogs = async () => {
  try {
    await fetch('/api/logs/clear', { method: 'POST' });
    logOutput.textContent = '';
  } catch (error) {
    console.error('Unable to clear logs', error);
  }
};

const loadCliData = async () => {
  const [metadataResponse, defaultsResponse] = await Promise.all([
    fetch('/api/cli-metadata'),
    fetch('/api/defaults'),
  ]);

  const metadataPayload = await metadataResponse.json();
  const defaultsPayload = await defaultsResponse.json();

  cliArguments = metadataPayload.arguments || [];
  defaultValues = defaultsPayload || {};
};

const initialize = async () => {
  try {
    await loadCliData();
    buildForm();
    await fetchStatus();
  } catch (error) {
    commandDisplay.textContent = 'Unable to initialize interface. Check server logs.';
    console.error(error);
  }

  startButton.addEventListener('click', (event) => {
    event.preventDefault();
    startProcess();
  });

  stopButton.addEventListener('click', (event) => {
    event.preventDefault();
    stopProcess();
  });

  clearLogButton.addEventListener('click', (event) => {
    event.preventDefault();
    clearLogs();
  });

  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
  pollingInterval = setInterval(fetchStatus, 2500);
};

initialize();
