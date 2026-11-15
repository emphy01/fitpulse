/**
 * FitPulse Home Workout Companion - Web Application Core JavaScript
 * Implements Nielsen 5 Usability Heuristics & Morville 7 UX Honeycomb
 */

// ============================================================================
// GLOBAL FETCH INTERCEPTOR (Attaches JWT Bearer Token to all /api/ requests)
// ============================================================================
(function() {
  const _nativeFetch = window.fetch;
  window.fetch = function(resource, init) {
    if (typeof resource === 'string' && resource.startsWith('/api')) {
      init = init ? { ...init } : {};
      const token = localStorage.getItem('fitpulse_token');
      if (token) {
        if (!init.headers) {
          init.headers = { 'Authorization': `Bearer ${token}` };
        } else if (init.headers instanceof Headers) {
          if (!init.headers.has('Authorization')) {
            init.headers.set('Authorization', `Bearer ${token}`);
          }
        } else if (Array.isArray(init.headers)) {
          init.headers.push(['Authorization', `Bearer ${token}`]);
        } else {
          if (!init.headers['Authorization']) {
            init.headers['Authorization'] = `Bearer ${token}`;
          }
        }
      }
    }
    return _nativeFetch(resource, init);
  };
})();

// ============================================================================
// AUDIO MANAGER (Web Audio API Synthesizer & Speech Synthesis TTS)
// ============================================================================
class AudioManager {
  constructor() {
    this.ctx = null;
    this.soundEnabled = true;
    this.voiceEnabled = true;
    this.voiceMode = 'voice'; // 'voice' (TTS) | 'chime' (Acoustic Chime Synth - No Google voice)
    this.selectedVoiceURI = '';
    this.pitch = 1.0;
    this.rate = 1.0;
    this.availableVoices = [];

    this._loadSettings();
    this._initVoices();
  }

  _loadSettings() {
    try {
      const saved = localStorage.getItem('fitpulse_audio_settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.voiceMode !== undefined) this.voiceMode = parsed.voiceMode;
        if (parsed.selectedVoiceURI !== undefined) this.selectedVoiceURI = parsed.selectedVoiceURI;
        if (parsed.pitch !== undefined) this.pitch = parseFloat(parsed.pitch);
        if (parsed.rate !== undefined) this.rate = parseFloat(parsed.rate);
      }
    } catch (e) {
      console.warn("Failed to load audio settings:", e);
    }
  }

  saveSettings() {
    try {
      const data = {
        voiceMode: this.voiceMode,
        selectedVoiceURI: this.selectedVoiceURI,
        pitch: this.pitch,
        rate: this.rate
      };
      localStorage.setItem('fitpulse_audio_settings', JSON.stringify(data));
    } catch (e) {
      console.warn("Failed to save audio settings:", e);
    }
  }

  _initVoices() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const loadVoices = () => {
        this.availableVoices = window.speechSynthesis.getVoices();
      };
      loadVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }
    }
  }

  _initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playBeep(freq = 880, duration = 0.08, type = 'sine') {
    if (!this.soundEnabled) return;
    try {
      this._initContext();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio play error:", e);
    }
  }

  playCountdown() {
    this.playBeep(880, 0.09, 'sine');
  }

  playGo() {
    this.playBeep(1200, 0.25, 'triangle');
  }

  playCelebration() {
    if (!this.soundEnabled) return;
    try {
      this._initContext();
      if (!this.ctx) return;

      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6 chord
      notes.forEach((freq, idx) => {
        setTimeout(() => {
          this.playBeep(freq, 0.3, 'triangle');
        }, idx * 120);
      });
    } catch (e) {
      console.warn("Celebration audio error:", e);
    }
  }

  playExerciseStartChime() {
    // Upbeat 3-tone ascending chord (G4, C5, E5)
    this._playMelody([392.00, 523.25, 659.25], [0.12, 0.12, 0.28]);
  }

  playRestChime() {
    // Gentle 2-tone descending relaxing chord (E5, B4)
    this._playMelody([659.25, 493.88], [0.16, 0.35]);
  }

  _playMelody(notes, durations) {
    if (!this.soundEnabled) return;
    try {
      this._initContext();
      if (!this.ctx) return;
      let timeOffset = 0;
      notes.forEach((freq, idx) => {
        const dur = durations[idx] || 0.15;
        setTimeout(() => {
          this.playBeep(freq, dur, 'triangle');
        }, timeOffset * 1000);
        timeOffset += dur * 0.85;
      });
    } catch (e) {
      console.warn("Melody error:", e);
    }
  }

  speak(text) {
    if (!this.voiceEnabled) return;

    // Mode 1: Chime / Acoustic Synth (No Google Voice, no speech synthesis)
    if (this.voiceMode === 'chime') {
      const lower = text.toLowerCase();
      if (lower.includes('istirahat') || lower.includes('rest')) {
        this.playRestChime();
      } else {
        this.playExerciseStartChime();
      }
      return;
    }

    // Mode 2: Voice TTS with custom selected voice, pitch, and speed
    if (!window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'id-ID';

      if (this.availableVoices.length === 0) {
        this.availableVoices = window.speechSynthesis.getVoices();
      }

      if (this.selectedVoiceURI && this.availableVoices.length > 0) {
        const found = this.availableVoices.find(v => v.voiceURI === this.selectedVoiceURI);
        if (found) {
          utter.voice = found;
          utter.lang = found.lang;
        }
      }

      utter.pitch = this.pitch || 1.0;
      utter.rate = this.rate || 1.0;
      window.speechSynthesis.speak(utter);
    } catch (e) {
      console.warn("Speech error:", e);
    }
  }
}

// ============================================================================
// MAIN APPLICATION CONTROLLER
// ============================================================================
class FitPulseApp {
  constructor() {
    this.audio = new AudioManager();
    
    // State
    this.profile = null;
    this.stats = null;
    this.routines = [];
    this.exercises = [];
    this.schedule = null;
    this.selectedRoutine = null;
    this.editingRoutineSteps = [];
    this.currentView = 'training';
    this.selectedMuscle = 'Semua';
    this.searchKeyword = '';

    // Active Workout Engine State
    this.workout = {
      active: false,
      paused: false,
      routine: null,
      steps: [],
      currentStepIndex: 0,
      stepRemainingSeconds: 0,
      totalElapsedSeconds: 0,
      caloriesBurned: 0.0,
      timerInterval: null,
      completedStepsCount: 0,
      lastFinishedLog: null
    };

    // Body Focus Categories
    this.muscleCategories = [
      { id: "Semua", label: "Semua" },
      { id: "Full Body", label: "Full Body" },
      { id: "Chest", label: "Dada (Chest)" },
      { id: "Abs & Core", label: "Perut (Abs)" },
      { id: "Arms", label: "Lengan (Arms)" },
      { id: "Legs", label: "Kaki (Legs)" },
      { id: "Back", label: "Punggung (Back)" }
    ];

    // Authenticated User State
    this.currentUser = null;
  }

  async init() {
    console.log("Initializing FitPulse Web App...");
    await this.checkAuthStatus();

    if (!this.currentUser) {
      // User must log in first before accessing the app
      this.openAuthModal('login');
      return;
    }

    await this.loadInitialData();
    this.setupMusclePills();
    this.setupWeeklyDots();
    this.navigate('training');
    
    // Lucide icon replacement
    if (window.lucide) {
      window.lucide.createIcons();
    }

    // Check if user has completed the onboarding profile setup
    if (this.profile && !this.profile.is_profile_completed) {
      this.openOnboardingProfileStep();
      return;
    }

    // Auto-display Onboarding Guide overlay on startup if enabled
    const hideGuide = localStorage.getItem('fitpulse_hide_guide') === 'true';
    const profileShowGuide = this.profile ? (this.profile.show_onboarding_guide !== false) : true;
    if (!hideGuide && profileShowGuide && !this.workout.active) {
      setTimeout(() => {
        this.openUserGuideOverlay(1);
      }, 400);
    }
  }

  // ==========================================================================
  // DATA FETCHING & API CALLS
  // ==========================================================================
  async loadInitialData() {
    try {
      const [todayRes, profileRes, statsRes, routinesRes, exercisesRes, scheduleRes] = await Promise.all([
        fetch('/api/today').then(r => r.json()),
        fetch('/api/profile').then(r => r.json()),
        fetch('/api/stats').then(r => r.json()),
        fetch('/api/routines').then(r => r.json()),
        fetch('/api/exercises').then(r => r.json()),
        fetch('/api/schedule').then(r => r.json())
      ]);

      this.profile = profileRes;
      this.stats = statsRes;
      this.routines = routinesRes;
      this.exercises = exercisesRes;
      this.schedule = scheduleRes;
      this.todayData = todayRes;

      // Update Audio preferences from profile
      this.audio.soundEnabled = Boolean(this.profile.sound_enabled);
      this.audio.voiceEnabled = Boolean(this.profile.voice_cues_enabled);

      // Update Header
      this.updateHeaderUI(todayRes);
      this.renderRoutines();
      this.renderTodayActivity();
      this.setupWeeklyDots();
      await this.renderHomePendingBanner();
      this.initAudioVoicesUI();
    } catch (err) {
      console.error("Error loading initial data:", err);
      this.showToast("Gagal memuat data dari server.", "error");
    }
  }

  async renderHomePendingBanner() {
    const container = document.getElementById('home-pending-workouts-container');
    if (!container) return;

    try {
      const res = await fetch('/api/pending_workouts');
      if (!res.ok) return;
      const list = await res.json();

      if (!list || list.length === 0) {
        container.innerHTML = '';
        return;
      }

      container.innerHTML = list.map(item => {
        const stepDisplay = (item.current_step_index || 0) + 1;
        const total = item.total_steps_count || 1;
        const pct = Math.round((stepDisplay / total) * 100);
        const mins = Math.floor((item.duration_spent_seconds || 0) / 60);

        return `
          <div class="bg-gradient-to-r from-amber-950/60 via-slate-900 to-slate-900 border border-amber-500/50 rounded-2xl p-4 sm:p-5 shadow-xl space-y-3">
            <div class="flex items-center justify-between">
              <span class="flex items-center gap-2 text-amber-400 font-extrabold text-xs sm:text-sm">
                <span class="text-base">⏸️</span>
                <span>SESI LATIHAN TERTUNDA</span>
              </span>
              <span class="text-[11px] bg-amber-500/20 text-amber-300 font-bold px-2.5 py-0.5 rounded-full border border-amber-500/40">
                Langkah ${stepDisplay}/${total} (${pct}%)
              </span>
            </div>
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div class="space-y-0.5">
                <h4 class="text-base font-bold text-white">${item.routine_title}</h4>
                <p class="text-xs text-slate-300">
                  Terhenti di gerakan ke-${stepDisplay} • Durasi berjalan: ${mins} menit • Kalori: <span class="text-amber-400 font-semibold">${item.calories_burned} kkal</span>
                </p>
                <p class="text-[11px] text-slate-400">
                  Sesi ini dapat dilanjutkan kapan saja tanpa mempengaruhi konsistensi mingguan Anda.
                </p>
              </div>
              <div class="flex items-center gap-2 pt-1 sm:pt-0 flex-shrink-0">
                <button 
                  onclick="app.resumePendingWorkout('${item.pending_id}')"
                  class="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 transition-all"
                >
                  <i data-lucide="play" class="w-3.5 h-3.5 fill-white"></i>
                  <span>Lanjutkan Sekarang</span>
                </button>
                <button 
                  onclick="app.restartPendingWorkout('${item.pending_id}')"
                  class="px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-semibold text-xs flex items-center gap-1 transition-all"
                  title="Mulai Ulang dari Langkah 1"
                >
                  <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                  <span>Mulai Ulang</span>
                </button>
                <button 
                  onclick="app.deletePendingWorkout('${item.pending_id}')"
                  class="p-2.5 rounded-xl bg-slate-800 hover:bg-red-950/60 text-slate-400 hover:text-red-400 text-xs transition-colors"
                  title="Hapus Sesi Tertunda"
                >
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');

      if (window.lucide) window.lucide.createIcons();
    } catch (e) {
      console.warn("Failed to render home pending banner:", e);
    }
  }

  updateHeaderUI(todayData) {
    if (!todayData) return;
    const streakEl = document.getElementById('header-streak-count');
    const userEl = document.getElementById('header-user-summary');

    if (streakEl) streakEl.innerText = todayData.streak_days || 0;
    
    const displayName = this.currentUser 
      ? (this.currentUser.name || this.currentUser.username)
      : (todayData.user_name || "Tamu");
    const weightDisplay = Math.round(todayData.weight_kg || (this.profile ? this.profile.weight_kg : 65));
    if (userEl) userEl.innerText = `${displayName} (${weightDisplay}kg)`;

    this.updateAuthUI();
  }

  // ==========================================================================
  // USER AUTHENTICATION & MULTI-USER CLOUD SYNC
  // ==========================================================================
  async checkAuthStatus() {
    const token = localStorage.getItem('fitpulse_token');
    if (!token) {
      this.currentUser = null;
      this.updateAuthUI();
      return null;
    }
    try {
      const res = await fetch('/api/auth/me');
      if (res.ok) {
        const authData = await res.json();
        if (authData.authenticated && authData.user) {
          this.currentUser = authData.user;
          this.profile = authData.profile || null;
        } else {
          localStorage.removeItem('fitpulse_token');
          this.currentUser = null;
        }
      } else {
        localStorage.removeItem('fitpulse_token');
        this.currentUser = null;
      }
    } catch (e) {
      console.warn("Check auth error:", e);
      this.currentUser = null;
    }
    this.updateAuthUI();
    return this.currentUser;
  }

  updateAuthUI() {
    const userMenu = document.getElementById('header-user-menu');
    const userSummary = document.getElementById('header-user-summary');
    const btnLogout = document.getElementById('btn-header-logout');

    // Settings view elements
    const statusBadge = document.getElementById('account-status-badge');
    const statusTitle = document.getElementById('account-status-title');
    const statusDesc = document.getElementById('account-status-desc');
    const btnAction = document.getElementById('btn-account-action');

    if (this.currentUser) {
      if (userMenu) userMenu.classList.remove('hidden');
      if (btnLogout) btnLogout.classList.remove('hidden');
      if (userSummary) {
        const displayName = this.profile?.name || this.currentUser.name || this.currentUser.username;
        const w = Math.round(this.profile ? this.profile.weight_kg : 65);
        userSummary.innerText = `${displayName} (${w}kg)`;
      }

      if (statusBadge) {
        statusBadge.className = "text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
        statusBadge.innerText = "Terhubung Cloud";
      }
      if (statusTitle) {
        statusTitle.innerText = `Akun: ${this.profile?.name || this.currentUser.name || this.currentUser.username}`;
      }
      if (statusDesc) {
        statusDesc.innerText = `Email: ${this.currentUser.email || '-'} • Data tersimpan aman di database cloud.`;
      }
      if (btnAction) {
        btnAction.onclick = () => this.logout();
        btnAction.innerHTML = '<i data-lucide="log-out" class="w-3.5 h-3.5"></i><span>Keluar Akun</span>';
        btnAction.className = "px-4 py-2 rounded-xl bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-800/60 font-bold text-xs transition-all shadow-md flex items-center justify-center gap-1.5 whitespace-nowrap";
      }
    } else {
      if (userMenu) userMenu.classList.add('hidden');
      if (btnLogout) btnLogout.classList.add('hidden');
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  openAuthModal(tab = 'login') {
    const modal = document.getElementById('modal-auth');
    if (modal) {
      modal.classList.remove('hidden');
      document.getElementById('auth-step-credentials')?.classList.remove('hidden');
      document.getElementById('auth-step-profile')?.classList.add('hidden');
      this.switchAuthTab(tab);
    }
    if (window.lucide) window.lucide.createIcons();
  }

  closeAuthModal() {
    const modal = document.getElementById('modal-auth');
    if (modal) {
      modal.classList.add('hidden');
    }
    const loginErr = document.getElementById('login-error-msg');
    const regErr = document.getElementById('register-error-msg');
    const onbErr = document.getElementById('onboard-error-msg');
    if (loginErr) { loginErr.classList.add('hidden'); loginErr.innerText = ''; }
    if (regErr) { regErr.classList.add('hidden'); regErr.innerText = ''; }
    if (onbErr) { onbErr.classList.add('hidden'); onbErr.innerText = ''; }
  }

  openOnboardingProfileStep() {
    const modal = document.getElementById('modal-auth');
    if (modal) {
      modal.classList.remove('hidden');
      document.getElementById('auth-step-credentials')?.classList.add('hidden');
      document.getElementById('auth-step-profile')?.classList.remove('hidden');

      // Pre-fill fields with current user data or sensible defaults
      const nameInput = document.getElementById('onboard-name');
      if (nameInput) {
        nameInput.value = this.profile?.name || (this.currentUser ? (this.currentUser.name || this.currentUser.username) : '');
      }
      const ageInput = document.getElementById('onboard-age');
      if (ageInput) ageInput.value = this.profile?.age || 22;
      const genderSelect = document.getElementById('onboard-gender');
      if (genderSelect) genderSelect.value = this.profile?.gender || 'pria';
      const heightInput = document.getElementById('onboard-height');
      if (heightInput) heightInput.value = this.profile?.height_cm || 170;
      const weightInput = document.getElementById('onboard-weight');
      if (weightInput) weightInput.value = this.profile?.weight_kg || 65;
      const fitnessSelect = document.getElementById('onboard-fitness-level');
      if (fitnessSelect) fitnessSelect.value = this.profile?.fitness_level || 'Beginner';
      const focusSelect = document.getElementById('onboard-target-focus');
      if (focusSelect) focusSelect.value = this.profile?.target_focus || 'Full Body';
    }
    if (window.lucide) window.lucide.createIcons();
  }

  switchAuthTab(tab) {
    const tabLogin = document.getElementById('auth-tab-login');
    const tabReg = document.getElementById('auth-tab-register');
    const formLogin = document.getElementById('form-login');
    const formReg = document.getElementById('form-register');

    if (tab === 'login') {
      if (tabLogin) tabLogin.className = "flex-1 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer bg-brand-600 text-white shadow-sm";
      if (tabReg) tabReg.className = "flex-1 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer text-slate-400 hover:text-white";
      if (formLogin) {
        formLogin.classList.remove('hidden');
        formLogin.style.display = 'block';
      }
      if (formReg) {
        formReg.classList.add('hidden');
        formReg.style.display = 'none';
      }
    } else {
      if (tabLogin) tabLogin.className = "flex-1 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer text-slate-400 hover:text-white";
      if (tabReg) tabReg.className = "flex-1 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer bg-emerald-600 text-white shadow-sm";
      if (formLogin) {
        formLogin.classList.add('hidden');
        formLogin.style.display = 'none';
      }
      if (formReg) {
        formReg.classList.remove('hidden');
        formReg.style.display = 'block';
      }
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }

  togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
  }

  async submitLogin(event) {
    if (event) event.preventDefault();
    const identifier = document.getElementById('login-identifier')?.value.trim();
    const password = document.getElementById('login-password')?.value;
    const errEl = document.getElementById('login-error-msg');
    const btnSubmit = document.getElementById('btn-submit-login');

    if (!identifier || !password) {
      if (errEl) {
        errEl.innerText = "Mohon masukkan email atau username dan kata sandi.";
        errEl.classList.remove('hidden');
      }
      return;
    }

    if (errEl) errEl.classList.add('hidden');
    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span>Memverifikasi Akun...</span>';
    }

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Login gagal.");
      }

      const authToken = data.token || data.access_token;
      if (authToken) {
        localStorage.setItem('fitpulse_token', authToken);
      }
      this.currentUser = data.user;
      await this.loadInitialData();

      // Check if user has already completed the onboarding profile setup
      if (this.profile && !this.profile.is_profile_completed) {
        this.openOnboardingProfileStep();
      } else {
        this.closeAuthModal();
        this.updateAuthUI();
        this.setupMusclePills();
        this.setupWeeklyDots();
        this.navigate('training');
        this.showToast(`Selamat datang kembali, ${this.profile?.name || data.user.name || data.user.username}!`, "success");
      }
    } catch (err) {
      if (errEl) {
        errEl.innerText = err.message || "Login gagal. Periksa kembali akun Anda.";
        errEl.classList.remove('hidden');
      }
    } finally {
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<span>Masuk Sekarang</span><i data-lucide="arrow-right" class="w-4 h-4"></i>';
        if (window.lucide) window.lucide.createIcons();
      }
    }
  }

  async submitRegister(event) {
    if (event) event.preventDefault();
    const name = document.getElementById('reg-name')?.value.trim();
    const username = document.getElementById('reg-username')?.value.trim();
    const email = document.getElementById('reg-email')?.value.trim();
    const password = document.getElementById('reg-password')?.value;
    const errEl = document.getElementById('register-error-msg');
    const btnSubmit = document.getElementById('btn-submit-register');

    if (!username || !email || !password) {
      if (errEl) {
        errEl.innerText = "Username, email, dan kata sandi wajib diisi.";
        errEl.classList.remove('hidden');
      }
      return;
    }

    if (errEl) errEl.classList.add('hidden');
    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span>Mendaftarkan Akun...</span>';
    }

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, name })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Pendaftaran gagal.");
      }

      const authToken = data.token || data.access_token;
      if (authToken) {
        localStorage.setItem('fitpulse_token', authToken);
      }
      this.currentUser = data.user;
      await this.loadInitialData();

      // Immediately proceed to Step 2: Onboarding Profile Form
      this.openOnboardingProfileStep();
      this.showToast(`Akun berhasil dibuat! Silakan lengkapi profil kebugaran Anda.`, "success");
    } catch (err) {
      if (errEl) {
        errEl.innerText = err.message || "Gagal membuat akun.";
        errEl.classList.remove('hidden');
      }
    } finally {
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<span>Daftar Akun Baru & Lanjut</span><i data-lucide="arrow-right" class="w-4 h-4"></i>';
        if (window.lucide) window.lucide.createIcons();
      }
    }
  }

  async submitOnboardingProfile(event) {
    if (event) event.preventDefault();
    const name = document.getElementById('onboard-name')?.value.trim();
    const age = parseInt(document.getElementById('onboard-age')?.value) || 22;
    const gender = document.getElementById('onboard-gender')?.value || 'pria';
    const height_cm = parseFloat(document.getElementById('onboard-height')?.value) || 170;
    const weight_kg = parseFloat(document.getElementById('onboard-weight')?.value) || 65;
    const fitness_level = document.getElementById('onboard-fitness-level')?.value || 'Beginner';
    const target_focus = document.getElementById('onboard-target-focus')?.value || 'Full Body';
    const errEl = document.getElementById('onboard-error-msg');
    const btnSubmit = document.getElementById('btn-submit-onboard');

    if (!name) {
      if (errEl) {
        errEl.innerText = "Nama lengkap wajib diisi.";
        errEl.classList.remove('hidden');
      }
      return;
    }

    if (errEl) errEl.classList.add('hidden');
    if (btnSubmit) {
      btnSubmit.disabled = true;
      btnSubmit.innerHTML = '<span>Menyimpan Profil...</span>';
    }

    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          age,
          gender,
          height_cm,
          weight_kg,
          fitness_level,
          target_focus,
          is_profile_completed: true
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Gagal menyimpan data profil.");
      }

      this.profile = data.profile;

      // Close the Auth & Onboarding Modal
      this.closeAuthModal();

      // Refresh app data and state
      await this.loadInitialData();
      this.setupMusclePills();
      this.setupWeeklyDots();
      this.navigate('training');
      this.updateAuthUI();

      // Now automatically trigger the User Guide overlay!
      setTimeout(() => {
        this.openUserGuideOverlay(1);
      }, 350);

      this.showToast(`Profil berhasil disimpan! Selamat datang, ${name}!`, "success");
    } catch (err) {
      if (errEl) {
        errEl.innerText = err.message || "Gagal menyimpan data ke server.";
        errEl.classList.remove('hidden');
      }
    } finally {
      if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<span>Simpan & Buka Panduan Pengguna</span><i data-lucide="arrow-right" class="w-4 h-4"></i>';
        if (window.lucide) window.lucide.createIcons();
      }
    }
  }

  async logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
      console.warn("Logout error:", e);
    }
    localStorage.removeItem('fitpulse_token');
    this.currentUser = null;
    this.profile = null;
    this.updateAuthUI();
    this.showToast("Anda telah keluar. Silakan masuk kembali.", "info");

    // Automatically return to Fullscreen Login Gate!
    this.openAuthModal('login');
  }

  renderTodayActivity() {
    const container = document.getElementById('today-activity-section');
    if (!container) return;

    const todayName = this.todayData?.today_day_name || "Hari Ini";
    const sched = this.todayData?.schedule || {};

    const isRest = Boolean(sched.is_rest_day) || !sched.routine_id;

    if (!isRest && sched.routine_id) {
      const routine = this.routines.find(r => r.id === sched.routine_id) || {
        id: sched.routine_id,
        title: sched.routine_title || "Latihan Terjadwal Hari Ini",
        description: "Program latihan sesuai jadwal mingguan Anda.",
        target_muscle: "Full Body",
        difficulty: "Optimal",
        steps: []
      };

      const durMins = Math.max(1, Math.round((routine.steps || []).reduce((sum, s) => sum + s.duration_seconds, 0) / 60)) || 15;
      const exCount = (routine.steps || []).filter(s => s.step_type === "Exercise").length || 8;

      container.innerHTML = `
        <div class="bg-gradient-to-r from-blue-900/60 via-indigo-900/40 to-slate-900 border border-blue-500/40 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1.5 flex-1 min-w-0">
            <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-bold">
              <span>📅 KEGIATAN HARI INI (${todayName.toUpperCase()})</span>
              <span>• ⏰ ${sched.scheduled_time || '07:00'}</span>
            </div>
            <h3 class="text-lg sm:text-xl font-extrabold text-white truncate">${routine.title}</h3>
            <p class="text-xs sm:text-sm text-slate-300">${durMins} Menit • ${exCount} Gerakan • ${routine.target_muscle} • ⚡ ${routine.difficulty}</p>
          </div>
          <button 
            onclick="app.openRoutineDetail('${routine.id}')"
            class="px-6 py-3.5 rounded-xl bg-gradient-to-r from-brand-500 to-blue-600 hover:from-brand-400 hover:to-blue-500 text-white font-extrabold text-xs sm:text-sm shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2 transition-all flex-shrink-0"
          >
            <i data-lucide="play" class="w-4 h-4 fill-white"></i>
            <span>Mulai Latihan Hari Ini</span>
          </button>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg flex items-center gap-4">
          <div class="w-12 h-12 rounded-2xl bg-sky-950 text-sky-400 border border-sky-800/40 flex items-center justify-center text-2xl flex-shrink-0 shadow-inner">
            🍃
          </div>
          <div class="flex-1 min-w-0">
            <span class="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">Kegiatan Hari Ini (${todayName})</span>
            <p class="text-sm font-semibold text-slate-200">Tidak ada jadwal latihan hari ini, tetap semangat dan beristirahatlah dengan nyaman.</p>
            <p class="text-xs text-slate-400 mt-0.5">Pemulihan otot sama pentingnya dengan latihan untuk memaksimalkan adaptasi tubuh.</p>
          </div>
        </div>
      `;
    }

    if (window.lucide) window.lucide.createIcons();
  }

  // ==========================================================================
  // VIEW NAVIGATION & ROUTING
  // ==========================================================================
  navigate(viewName) {
    // If in active workout and navigating away, confirm first
    if (this.workout.active && viewName !== 'active-workout') {
      this.promptAbortWorkout(() => {
        this._doNavigate(viewName);
      });
      return;
    }

    this._doNavigate(viewName);
  }

  _doNavigate(viewName) {
    this.currentView = viewName;

    // Hide all views
    document.querySelectorAll('.app-view').forEach(el => el.classList.add('hidden'));

    // Show target view
    const targetEl = document.getElementById(`view-${viewName}`);
    if (targetEl) {
      targetEl.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Sync Desktop Nav tabs
    document.querySelectorAll('.nav-desktop-tab').forEach(btn => btn.classList.remove('active'));
    const desktopBtn = document.getElementById(`nav-btn-${viewName}`);
    if (desktopBtn) desktopBtn.classList.add('active');

    // Sync Mobile Bottom Nav buttons
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => btn.classList.remove('active'));
    const mobileBtn = document.getElementById(`mobile-nav-${viewName}`);
    if (mobileBtn) mobileBtn.classList.add('active');

    // Trigger View-specific Refresh
    if (viewName === 'training') {
      this.renderRoutines();
    } else if (viewName === 'report') {
      this.renderReportView();
    } else if (viewName === 'settings') {
      this.renderSettingsView();
    }

    // Refresh icons
    if (window.lucide) window.lucide.createIcons();
  }

  // ==========================================================================
  // VIEW 1: TRAINING HUB & ROUTINES
  // ==========================================================================
  setupMusclePills() {
    const container = document.getElementById('muscle-filter-pills');
    if (!container) return;

    container.innerHTML = this.muscleCategories.map(cat => `
      <button 
        onclick="app.onSelectMuscle('${cat.id}')"
        class="muscle-filter-pill px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border ${
          this.selectedMuscle === cat.id 
            ? 'active bg-brand-600 text-white border-brand-400' 
            : 'bg-slate-900/90 text-slate-300 border-slate-800 hover:border-slate-700'
        }"
      >
        ${cat.label}
      </button>
    `).join('');
  }

  onSelectMuscle(muscleId) {
    this.selectedMuscle = muscleId;
    this.setupMusclePills();
    this.renderRoutines();
  }

  onSearchInput(val) {
    this.searchKeyword = val.trim();
    const clearBtn = document.getElementById('search-clear-btn');
    if (clearBtn) {
      if (this.searchKeyword) clearBtn.classList.remove('hidden');
      else clearBtn.classList.add('hidden');
    }
    this.renderRoutines();
  }

  clearSearch() {
    const input = document.getElementById('search-input');
    if (input) input.value = '';
    this.searchKeyword = '';
    const clearBtn = document.getElementById('search-clear-btn');
    if (clearBtn) clearBtn.classList.add('hidden');
    this.renderRoutines();
  }

  setupWeeklyDots() {
    const dayNames = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];
    const shortNames = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"];
    const container = document.getElementById('weekly-days-strip');

    // 1. Consistency & Target Count
    const consist = this.todayData?.consistency || this.stats?.consistency || {};
    const completed = consist.completed_this_week ?? 0;
    const totalTarget = consist.total_scheduled_week ?? 0;
    const completedDays = consist.completed_day_names || [];

    const goalStatusEl = document.getElementById('weekly-goal-status');
    if (goalStatusEl) {
      if (totalTarget === 0) {
        goalStatusEl.innerText = "0/0 Hari";
        goalStatusEl.title = "Semua hari disetel sebagai Hari Istirahat";
      } else {
        goalStatusEl.innerText = `${completed}/${totalTarget} Hari`;
        goalStatusEl.title = `${completed} dari ${totalTarget} hari latihan mingguan selesai`;
      }
    }

    if (!container) return;

    // Today index (0 = Monday, 6 = Sunday)
    const rawDay = new Date().getDay();
    const todayIdx = rawDay === 0 ? 6 : rawDay - 1;

    container.innerHTML = dayNames.map((fullName, idx) => {
      const shortName = shortNames[idx];
      const isToday = (idx === todayIdx);
      const schedDay = this.schedule?.days?.[fullName];
      const isRest = schedDay ? Boolean(schedDay.is_rest_day) : false;
      const isCompleted = completedDays.includes(fullName);

      let circleClass = '';
      let circleContent = '';
      let subLabel = '';

      if (isRest) {
        circleClass = isToday 
          ? 'bg-sky-950/60 border-2 border-sky-400 text-sky-300' 
          : 'bg-sky-950/30 border border-sky-900/40 text-sky-400/80';
        circleContent = '💤';
        subLabel = `<span class="text-[9px] ${isToday ? 'text-sky-300 font-bold' : 'text-sky-400/70'}">Rest</span>`;
      } else if (isCompleted) {
        circleClass = 'bg-brand-500 text-white shadow-md shadow-brand-500/30 border border-brand-400';
        circleContent = '✓';
        subLabel = `<span class="text-[9px] text-brand-400 font-bold">Done</span>`;
      } else if (isToday) {
        circleClass = 'border-2 border-brand-400 text-brand-400 bg-slate-900 font-black shadow-sm';
        circleContent = String(idx + 1);
        subLabel = `<span class="text-[9px] text-brand-400 font-bold">Hari Ini</span>`;
      } else {
        circleClass = 'bg-slate-800/80 text-slate-400 border border-slate-700/60';
        circleContent = String(idx + 1);
        subLabel = `<span class="text-[9px] text-slate-500">Latihan</span>`;
      }

      const tooltipText = isRest 
        ? `${fullName}: Hari Istirahat` 
        : `${fullName}: ${schedDay?.routine_title || 'Latihan'}${isCompleted ? ' (Selesai ✓)' : ''}`;

      return `
        <div class="flex flex-col items-center gap-1 cursor-default group" title="${tooltipText}">
          <span class="text-[11px] font-semibold ${isToday ? 'text-brand-400 font-bold' : 'text-slate-400'}">${shortName}</span>
          <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-transform group-hover:scale-105 ${circleClass}">
            ${circleContent}
          </div>
          ${subLabel}
        </div>
      `;
    }).join('');
  }

  renderRoutines() {
    const container = document.getElementById('routines-grid');
    const badge = document.getElementById('routines-count-badge');
    if (!container) return;

    let filtered = this.routines;

    // Muscle Filter
    if (this.selectedMuscle !== 'Semua') {
      filtered = filtered.filter(r => r.target_muscle.toLowerCase() === this.selectedMuscle.toLowerCase());
    }

    // Keyword search
    if (this.searchKeyword) {
      const kw = this.searchKeyword.toLowerCase();
      filtered = filtered.filter(r => 
        r.title.toLowerCase().includes(kw) || 
        r.description.toLowerCase().includes(kw) ||
        r.target_muscle.toLowerCase().includes(kw)
      );
    }

    if (badge) badge.innerText = filtered.length;

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="col-span-full py-12 text-center bg-slate-900/60 rounded-2xl border border-slate-800">
          <span class="text-4xl block mb-2">🔍</span>
          <h4 class="text-sm font-bold text-slate-300">Tidak ada latihan yang cocok</h4>
          <p class="text-xs text-slate-500 mt-1">Coba ganti filter otot atau kata kunci pencarian Anda.</p>
        </div>
      `;
      return;
    }

    // Difficulty lightning bolts
    const boltMap = {
      "Beginner": "⚡ Beginner",
      "Intermediate": "⚡⚡ Intermediate",
      "Advanced": "⚡⚡⚡ Advanced"
    };

    container.innerHTML = filtered.map(r => {
      // Find cover image or fallback to 1:1 image from first exercise
      let coverImg = "/images/covers/cover_default_custom.png";
      if (r.cover_image) {
        coverImg = "/" + r.cover_image.replace(/\\/g, '/');
      } else if (r.steps && r.steps.length > 0) {
        for (const st of r.steps) {
          if (st.exercise && st.exercise.image_path) {
            coverImg = "/" + st.exercise.image_path.replace(/\\/g, '/');
            break;
          }
        }
      }

      const durMins = Math.max(1, Math.round(r.steps.reduce((sum, s) => sum + s.duration_seconds, 0) / 60));
      const exCount = r.steps.filter(s => s.step_type === "Exercise").length;

      return `
        <div 
          onclick="app.openRoutineDetail('${r.id}')"
          class="group bg-gradient-to-br from-slate-900 to-slate-850 hover:to-slate-800 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-4 cursor-pointer transition-all duration-200 transform hover:-translate-y-1 shadow-lg hover:shadow-xl flex items-center justify-between gap-3"
        >
          <div class="flex items-center gap-3.5 flex-1 min-w-0">
            <!-- Routine Cover Thumbnail (16:9 ratio) -->
            <div class="w-20 h-14 rounded-xl bg-slate-950 border border-slate-800 flex-shrink-0 overflow-hidden flex items-center justify-center shadow-inner">
              <img src="${coverImg}" alt="${r.title}" class="w-full h-full object-cover group-hover:scale-105 transition-transform" onerror="this.onerror=null; this.src='/images/covers/cover_default_custom.png'" />
            </div>

            <!-- Routine Info Column -->
            <div class="min-w-0 flex-1">
              <h3 class="font-bold text-sm sm:text-base text-white truncate group-hover:text-brand-400 transition-colors">${r.title}</h3>
              <p class="text-xs text-slate-400 mt-0.5">${durMins} Menit • ${exCount} Gerakan • ${r.target_muscle}</p>
              <span class="inline-block mt-1 text-[11px] font-bold text-sky-400">
                ${boltMap[r.difficulty] || r.difficulty}
              </span>
            </div>
          </div>

          <!-- Clean Chevron (No clutter button) -->
          <div class="text-slate-500 group-hover:text-brand-400 text-2xl font-bold transition-transform group-hover:translate-x-1 pr-1">
            ›
          </div>
        </div>
      `;
    }).join('');
  }

  startQuickStart() {
    // Look for 7-minute routine
    const qRoutine = this.routines.find(r => r.id === "routine_7min_fullbody") || this.routines[0];
    if (qRoutine) {
      this.openRoutineDetail(qRoutine.id);
    }
  }

  // ==========================================================================
  // VIEW 2: ROUTINE DETAIL / PLAN OVERVIEW
  // ==========================================================================
  async openRoutineDetail(routineId) {
    try {
      const res = await fetch(`/api/routines/${routineId}`);
      if (!res.ok) throw new Error("Program tidak ditemukan");
      const routine = await res.json();

      this.selectedRoutine = routine;

      // Populate Detail Screen UI
      const coverEl = document.getElementById('detail-cover-img');
      if (coverEl) {
        let coverSrc = routine.cover_image ? "/" + routine.cover_image.replace(/\\/g, '/') : `/images/covers/cover_${routine.id}.png`;
        coverEl.src = coverSrc;
      }

      document.getElementById('detail-routine-title').innerText = routine.title;
      document.getElementById('detail-routine-desc').innerText = routine.description;
      document.getElementById('detail-target-muscle').innerText = routine.target_muscle.toUpperCase();
      document.getElementById('detail-muscle-text').innerText = routine.target_muscle;
      document.getElementById('detail-difficulty-badge').innerText = `⚡ ${routine.difficulty}`;
      document.getElementById('detail-difficulty-text').innerText = routine.difficulty;

      const durMins = Math.max(1, Math.round(routine.steps.reduce((sum, s) => sum + s.duration_seconds, 0) / 60));
      const exCount = routine.steps.filter(s => s.step_type === "Exercise").length;

      document.getElementById('detail-duration').innerText = `${durMins} Menit`;
      document.getElementById('detail-exercise-count').innerText = `${exCount} Gerakan`;

      // Render Exercise List
      const listContainer = document.getElementById('detail-exercise-list');
      let stepNum = 1;

      listContainer.innerHTML = routine.steps.map(st => {
        if (st.step_type !== 'Exercise' || !st.exercise) return '';

        const ex = st.exercise;
        const iconPath = "/" + (ex.icon_path || "workout_data/images/icons/icon_" + ex.id + ".png").replace(/\\/g, '/');
        const imgPath = "/" + (ex.image_path || "workout_data/images/jumping_jacks.png").replace(/\\/g, '/');
        const isRep = Boolean(st.target_reps || ex.is_reps_based);
        const badgeText = isRep ? `×${st.target_reps || ex.default_reps || 12}` : `${st.duration_seconds}s`;

        const curStep = stepNum++;

        return `
          <div 
            onclick="app.openExerciseGuideModal('${ex.id}')"
            class="group bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl p-3 flex items-center justify-between gap-3 cursor-pointer transition-all hover:border-slate-700"
          >
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <span class="text-slate-500 font-bold text-xs w-4">${curStep}.</span>

              <!-- Exercise Icon / 1:1 Thumbnail (52x52) -->
              <div class="w-12 h-12 rounded-lg bg-slate-950 border border-slate-800 flex-shrink-0 overflow-hidden flex items-center justify-center">
                <img src="${iconPath}" alt="${ex.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform" onerror="this.onerror=null; this.src='${imgPath}'" />
              </div>

              <div class="min-w-0 flex-1">
                <h4 class="font-bold text-sm text-white truncate group-hover:text-brand-400 transition-colors">${ex.name}</h4>
                <p class="text-xs text-slate-400 truncate">Fokus: ${ex.focus_areas && ex.focus_areas.length ? ex.focus_areas.slice(0, 2).join(', ') : ex.target_muscle}</p>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <span class="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 text-xs font-bold font-mono border border-slate-700">
                ${badgeText}
              </span>
              <button 
                onclick="event.stopPropagation(); app.openExerciseGuideModal('${ex.id}')"
                class="px-2 py-1 rounded-lg text-brand-400 hover:text-white hover:bg-slate-800 text-xs font-semibold flex items-center gap-1 transition-colors"
                title="Buka Panduan Gerakan"
              >
                <span>ℹ️</span>
                <span class="hidden sm:inline">Panduan</span>
              </button>
            </div>
          </div>
        `;
      }).join('');

      this.navigate('routine-detail');
    } catch (e) {
      console.error(e);
      this.showToast("Gagal memuat detail program latihan.", "error");
    }
  }

  // ==========================================================================
  // VIEW 3: ACTIVE WORKOUT RUNNER (STATE MACHINE & TIMER)
  // ==========================================================================
  startActiveWorkout() {
    if (!this.selectedRoutine) return;

    this.workout.active = true;
    this.workout.paused = false;
    this.workout.routine = this.selectedRoutine;
    this.workout.steps = [...this.selectedRoutine.steps];
    this.workout.currentStepIndex = 0;
    this.workout.totalElapsedSeconds = 0;
    this.workout.caloriesBurned = 0.0;
    this.workout.completedStepsCount = 0;

    // Setup first step
    this.setupCurrentStep();

    // Navigate to active workout view
    this._doNavigate('active-workout');

    // Start timer loop
    this.startWorkoutTimer();

    // Sound / Voice cue
    this.audio.playGo();
    const cur = this.getCurrentStep();
    if (cur && cur.exercise) {
      this.audio.speak(`Mulai latihan: ${cur.exercise.name}`);
    }
  }

  getCurrentStep() {
    return this.workout.steps[this.workout.currentStepIndex] || null;
  }

  getNextStep() {
    return this.workout.steps[this.workout.currentStepIndex + 1] || null;
  }

  setupCurrentStep() {
    const step = this.getCurrentStep();
    if (!step) {
      this.finishActiveWorkout();
      return;
    }

    this.workout.stepRemainingSeconds = step.duration_seconds;
    this.renderWorkoutScreen();
  }

  renderWorkoutScreen() {
    const step = this.getCurrentStep();
    const next = this.getNextStep();
    if (!step) return;

    const isRest = (step.step_type === 'Rest');
    const isRep = Boolean(step.target_reps || (step.exercise && step.exercise.is_reps_based)) && !isRest;

    // Header labels
    document.getElementById('live-routine-title').innerText = this.workout.routine.title;
    document.getElementById('live-step-badge').innerText = `Langkah ${this.workout.currentStepIndex + 1}/${this.workout.steps.length}`;

    // Progress bar
    const pct = Math.round((this.workout.currentStepIndex / this.workout.steps.length) * 100);
    document.getElementById('live-progress-bar').style.width = `${pct}%`;

    // Image Resolution (Supports direct path, ID derivation, and clean fallbacks)
    const imgEl = document.getElementById('live-exercise-image');
    const placeholderEl = document.getElementById('live-image-placeholder');
    let imgSource = "";
    if (isRest) {
      if (next && next.exercise) {
        imgSource = next.exercise.image_path || `workout_data/images/${next.exercise.id}.png`;
      }
    } else if (step.exercise) {
      imgSource = step.exercise.image_path || `workout_data/images/${step.exercise.id}.png`;
    }

    if (imgSource) {
      let cleanSrc = imgSource.replace(/\\/g, '/');
      if (!cleanSrc.startsWith('/')) cleanSrc = '/' + cleanSrc;
      imgEl.src = cleanSrc;
      imgEl.classList.remove('hidden');
      if (placeholderEl) placeholderEl.classList.add('hidden');
    } else {
      imgEl.src = "/workout_data/images/ex_jumping_jacks.png";
      imgEl.classList.remove('hidden');
      if (placeholderEl) placeholderEl.classList.add('hidden');
    }
    imgEl.onerror = function() {
      if (this.src && this.src.indexOf('ex_jumping_jacks.png') === -1) {
        this.src = "/workout_data/images/ex_jumping_jacks.png";
      } else {
        this.classList.add('hidden');
        if (placeholderEl) placeholderEl.classList.remove('hidden');
      }
    };

    // Exercise Icons: Current active exercise icon & next exercise icon
    const iconEl = document.getElementById('live-exercise-icon');
    const nextIconEl = document.getElementById('live-next-icon');

    let iconSrc = "/workout_data/images/icons/icon_ex_jumping_jacks.png";
    if (isRest) {
      iconSrc = "/workout_data/images/icons/icon_rest.png";
    } else if (step.exercise) {
      let rawIcon = step.exercise.icon_path || `workout_data/images/icons/icon_${step.exercise.id}.png`;
      let cleanIcon = rawIcon.replace(/\\/g, '/');
      if (!cleanIcon.startsWith('/')) cleanIcon = '/' + cleanIcon;
      iconSrc = cleanIcon;
    }
    if (iconEl) {
      iconEl.src = iconSrc;
      iconEl.onerror = function() {
        this.onerror = null;
        this.src = "/workout_data/images/icons/icon_ex_jumping_jacks.png";
      };
    }

    if (nextIconEl) {
      if (next && next.exercise) {
        let rawNext = next.exercise.icon_path || `workout_data/images/icons/icon_${next.exercise.id}.png`;
        let cleanNext = rawNext.replace(/\\/g, '/');
        if (!cleanNext.startsWith('/')) cleanNext = '/' + cleanNext;
        nextIconEl.src = cleanNext;
        nextIconEl.classList.remove('hidden');
        nextIconEl.onerror = function() {
          this.onerror = null;
          this.src = "/workout_data/images/icons/icon_ex_jumping_jacks.png";
        };
      } else {
        nextIconEl.classList.add('hidden');
      }
    }

    // Title & status pill
    const nameEl = document.getElementById('live-exercise-name');
    const pillEl = document.getElementById('live-status-pill');

    if (isRest) {
      nameEl.innerText = "ISTIRAHAT (REST)";
      pillEl.innerText = "🍃 ISTIRAHAT & PEMULIHAN";
      pillEl.className = "inline-block px-3 py-0.5 rounded-full text-xs font-extrabold uppercase bg-sky-500/20 text-sky-400 border border-sky-500/30";
    } else if (isRep) {
      nameEl.innerText = step.exercise ? step.exercise.name : "Gerakan Repetisi";
      pillEl.innerText = "💪 LATIHAN REPETISI";
      pillEl.className = "inline-block px-3 py-0.5 rounded-full text-xs font-extrabold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    } else {
      nameEl.innerText = step.exercise ? step.exercise.name : "Latihan Aktif";
      pillEl.innerText = "💪 LATIHAN AKTIF";
      pillEl.className = "inline-block px-3 py-0.5 rounded-full text-xs font-extrabold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    }

    // Big timer / Reps display
    const timerEl = document.getElementById('live-timer-display');
    if (isRep) {
      timerEl.innerText = `×${step.target_reps || step.exercise.default_reps || 12}`;
    } else {
      timerEl.innerText = `${this.workout.stepRemainingSeconds}s`;
    }

    // Calories & Next
    const calEl = document.getElementById('live-calories-burned');
    if (calEl) {
      if (this.workout.paused) {
        calEl.innerText = `Terjeda: ${this.workout.caloriesBurned.toFixed(1)} kkal`;
      } else {
        calEl.innerText = "Kalori dihitung saat jeda/selesai";
      }
    }
    const nextName = next ? (next.exercise ? next.exercise.name : 'Istirahat') : 'Selesai';
    document.getElementById('live-next-exercise-name').innerText = nextName;

    // Toggle Controls Container (Time-based vs Reps vs Rest)
    const ctrlTime = document.getElementById('controls-time-based');
    const ctrlRep = document.getElementById('controls-rep-based');
    const ctrlRest = document.getElementById('controls-rest');

    ctrlTime.classList.add('hidden');
    ctrlRep.classList.add('hidden');
    ctrlRest.classList.add('hidden');

    if (isRest) {
      ctrlRest.classList.remove('hidden');
    } else if (isRep) {
      ctrlRep.classList.remove('hidden');
    } else {
      ctrlTime.classList.remove('hidden');
      this.updatePauseButtonUI();
    }
  }

  startWorkoutTimer() {
    clearInterval(this.workout.timerInterval);
    this.workout.timerInterval = setInterval(() => {
      this.onTimerTick();
    }, 1000);
  }

  onTimerTick() {
    if (!this.workout.active || this.workout.paused) return;

    this.workout.totalElapsedSeconds += 1;

    const step = this.getCurrentStep();
    if (!step) return;

    // Calculate incremental calories using ACSM MET formula
    const weight = this.profile?.weight_kg || 65.0;
    const met = (step.step_type === 'Rest') ? 1.3 : (step.exercise?.met_value || 6.0);
    const calsPerSec = ((met * 3.5 * weight) / 200.0) / 60.0;
    this.workout.caloriesBurned += calsPerSec;

    // Time-based steps count down
    const isRep = Boolean(step.target_reps || (step.exercise && step.exercise.is_reps_based)) && step.step_type !== 'Rest';

    if (!isRep) {
      this.workout.stepRemainingSeconds -= 1;

      // Audio beeps on 3, 2, 1
      if (this.workout.stepRemainingSeconds === 3 || this.workout.stepRemainingSeconds === 2 || this.workout.stepRemainingSeconds === 1) {
        this.audio.playCountdown();
      }

      if (this.workout.stepRemainingSeconds <= 0) {
        this.audio.playGo();
        this.advanceToNextStep();
        return;
      }
    }

    const calEl = document.getElementById('live-calories-burned');
    if (calEl && !this.workout.paused) {
      calEl.innerText = "Kalori dihitung saat jeda/selesai";
    }

    this.renderWorkoutScreen();
  }

  advanceToNextStep() {
    this.workout.completedStepsCount += 1;
    this.workout.currentStepIndex += 1;

    if (this.workout.currentStepIndex >= this.workout.steps.length) {
      this.finishActiveWorkout();
    } else {
      this.setupCurrentStep();
      const cur = this.getCurrentStep();
      if (cur && cur.exercise) {
        this.audio.speak(cur.exercise.name);
      } else if (cur && cur.step_type === 'Rest') {
        this.audio.speak("Waktunya istirahat");
      }
    }
  }

  togglePauseResume() {
    this.workout.paused = !this.workout.paused;
    this.updatePauseButtonUI();

    const calEl = document.getElementById('live-calories-burned');
    if (this.workout.paused) {
      if (calEl) calEl.innerText = `Terjeda: ${this.workout.caloriesBurned.toFixed(1)} kkal`;
      this.showToast(`⏸️ Latihan terjeda. Pembakaran lemak saat ini: ${this.workout.caloriesBurned.toFixed(1)} kkal`, "info");
    } else {
      if (calEl) calEl.innerText = "Kalori dihitung saat jeda/selesai";
    }
  }

  updatePauseButtonUI() {
    const btn = document.getElementById('btn-pause-resume');
    const txt = document.getElementById('pause-text');
    const icon = document.getElementById('pause-icon');
    const pausedBanner = document.getElementById('live-paused-banner');
    const bannerText = document.getElementById('paused-status-banner-text');

    if (!btn || !txt) return;

    if (this.workout.paused) {
      btn.className = "flex-1 max-w-[160px] py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm sm:text-base flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30 transition-all";
      txt.innerText = "Lanjut ▶";
      if (icon) icon.setAttribute('data-lucide', 'play');

      if (pausedBanner) {
        pausedBanner.classList.remove('hidden');
        if (bannerText) {
          bannerText.innerText = `Sesi Latihan Terjeda • Kalori terbakar: ${this.workout.caloriesBurned.toFixed(1)} kkal`;
        }
      }
    } else {
      btn.className = "flex-1 max-w-[160px] py-3.5 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-sm sm:text-base flex items-center justify-center gap-2 shadow-lg shadow-brand-600/30 transition-all";
      txt.innerText = "Pause ⏸";
      if (icon) icon.setAttribute('data-lucide', 'pause');

      if (pausedBanner) {
        pausedBanner.classList.add('hidden');
      }
    }
    if (window.lucide) window.lucide.createIcons();
  }

  skipStep() {
    this.advanceToNextStep();
  }

  prevStep() {
    if (this.workout.currentStepIndex > 0) {
      this.workout.currentStepIndex -= 1;
      this.setupCurrentStep();
    }
  }

  adjustTime(seconds) {
    this.workout.stepRemainingSeconds = Math.max(1, this.workout.stepRemainingSeconds + seconds);
    this.renderWorkoutScreen();
    this.showToast(`+${seconds} Detik`, "info");
  }

  // ==========================================================================
  // CELEBRATION & WORKOUT COMPLETION
  // ==========================================================================
  async finishActiveWorkout() {
    clearInterval(this.workout.timerInterval);
    this.workout.active = false;

    // Trigger Confetti
    if (window.confetti) {
      window.confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      });
    }

    this.audio.playCelebration();

    // Prepare Log
    const totalRoutineDuration = this.workout.routine.steps.reduce((s, st) => s + st.duration_seconds, 0);
    const logData = {
      routine_id: this.workout.routine.id,
      routine_title: this.workout.routine.title,
      duration_spent_seconds: this.workout.totalElapsedSeconds,
      total_routine_duration_seconds: totalRoutineDuration,
      calories_burned: Math.round(this.workout.caloriesBurned * 10) / 10,
      completed_steps_count: this.workout.steps.length,
      total_steps_count: this.workout.steps.length,
      status: "COMPLETED"
    };

    try {
      const res = await fetch('/api/session/save_log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData)
      });
      const data = await res.json();
      this.workout.lastFinishedLog = data.log;

      // Populate celebration screen
      const mins = Math.floor(this.workout.totalElapsedSeconds / 60);
      const secs = this.workout.totalElapsedSeconds % 60;
      document.getElementById('celeb-routine-name').innerText = this.workout.routine.title;
      document.getElementById('celeb-duration').innerText = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
      document.getElementById('celeb-calories').innerText = `${this.workout.caloriesBurned.toFixed(1)} kkal`;
      document.getElementById('celeb-completion').innerText = "100%";

      // Show adaptive advice
      const adviceCard = document.getElementById('adaptive-advice-card');
      const adviceText = document.getElementById('adaptive-advice-text');
      if (data.recommendation && adviceCard && adviceText) {
        adviceText.innerText = data.recommendation;
        adviceCard.classList.remove('hidden');
      }

      this._doNavigate('celebration');
      this.showToast(`Selamat, Anda menyelesaikan latihan hari ini! Kalori terbakar: ${this.workout.caloriesBurned.toFixed(1)} kkal`, "success");
      this.loadInitialData(); // Refresh streak & stats
    } catch (e) {
      console.error(e);
      this.showToast("Gagal menyimpan riwayat workout.", "error");
    }
  }

  async submitFeedback(feeling) {
    if (!this.workout.lastFinishedLog) return;

    try {
      const res = await fetch('/api/session/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          log_id: this.workout.lastFinishedLog.log_id,
          user_feedback: feeling
        })
      });
      const data = await res.json();

      const adviceCard = document.getElementById('adaptive-advice-card');
      const adviceText = document.getElementById('adaptive-advice-text');
      if (adviceCard && adviceText) {
        adviceText.innerText = data.advice;
        adviceCard.classList.remove('hidden');
      }

      // Highlight selected feeling button
      document.querySelectorAll('.feedback-btn').forEach(btn => btn.classList.remove('border-brand-500', 'bg-brand-500/20'));
      this.showToast("Terima kasih atas masukan evaluasi Anda!", "success");
    } catch (e) {
      console.error(e);
    }
  }

  promptAbortWorkout(onConfirmCallback = null) {
    this.abortCallback = onConfirmCallback;
    this.openModal('modal-confirm-abort');
  }

  async executeSavePendingWorkout() {
    this.closeModal('modal-confirm-abort');
    clearInterval(this.workout.timerInterval);
    this.workout.active = false;

    const pendingData = {
      routine_id: this.workout.routine.id,
      routine_title: this.workout.routine.title,
      current_step_index: this.workout.currentStepIndex,
      total_steps_count: this.workout.steps.length,
      duration_spent_seconds: this.workout.totalElapsedSeconds,
      calories_burned: Math.round(this.workout.caloriesBurned * 10) / 10
    };

    try {
      const res = await fetch('/api/pending_workouts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pendingData)
      });
      if (!res.ok) throw new Error("Gagal menyimpan ke server");
      this.showToast(`Latihan disimpan ke 'Pelatihan Tertunda'. Kalori terbakar saat ini: ${pendingData.calories_burned} kkal.`, "success");
      await this.loadInitialData();
    } catch (e) {
      console.error(e);
      this.showToast("Gagal menyimpan pelatihan tertunda: " + e.message, "error");
    }

    if (this.abortCallback) {
      this.abortCallback();
      this.abortCallback = null;
    } else {
      this._doNavigate('training');
    }
  }

  async executeAbortWorkout() {
    this.closeModal('modal-confirm-abort');
    clearInterval(this.workout.timerInterval);
    this.workout.active = false;

    // Save partial progress
    const logData = {
      routine_id: this.workout.routine.id,
      routine_title: this.workout.routine.title,
      duration_spent_seconds: this.workout.totalElapsedSeconds,
      total_routine_duration_seconds: this.workout.routine.steps.reduce((s, st) => s + st.duration_seconds, 0),
      calories_burned: Math.round(this.workout.caloriesBurned * 10) / 10,
      completed_steps_count: this.workout.currentStepIndex,
      total_steps_count: this.workout.steps.length,
      status: "ABORTED"
    };

    try {
      await fetch('/api/session/save_log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData)
      });
      this.showToast(`Latihan dibatalkan. Kalori terbakar: ${logData.calories_burned} kkal.`, "info");
      this.loadInitialData();
    } catch (e) {
      console.error(e);
    }

    if (this.abortCallback) {
      this.abortCallback();
      this.abortCallback = null;
    } else {
      this._doNavigate('training');
    }
  }

  async renderPendingWorkouts() {
    const container = document.getElementById('pending-workouts-list');
    const badge = document.getElementById('pending-count-badge');
    if (!container) return;

    try {
      const res = await fetch('/api/pending_workouts');
      const list = await res.json();

      if (badge) badge.innerText = list ? list.length : 0;

      if (!list || list.length === 0) {
        container.innerHTML = `
          <div class="py-4 text-center text-slate-500 text-xs">
            Tidak ada pelatihan yang tertunda saat ini.
          </div>
        `;
        return;
      }

      container.innerHTML = list.map(item => {
        const stepDisplay = (item.current_step_index || 0) + 1;
        const total = item.total_steps_count || 1;
        const pct = Math.round((stepDisplay / total) * 100);
        const mins = Math.floor((item.duration_spent_seconds || 0) / 60);

        let dateStr = item.timestamp || "";
        try {
          const d = new Date(item.timestamp);
          dateStr = d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
        } catch (e) {}

        return `
          <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
            <div class="flex items-center justify-between text-xs font-bold">
              <span class="text-amber-400 flex items-center gap-1.5">
                <span>⏸️</span>
                <span>${item.routine_title}</span>
              </span>
              <span class="text-slate-400 text-[11px] font-normal">${dateStr}</span>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div class="bg-amber-500 h-1.5 rounded-full" style="width: ${pct}%;"></div>
            </div>

            <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-400 gap-2">
              <span>Terhenti di Langkah ${stepDisplay}/${total} (${pct}%) • ${mins} mnt berjalan • 🔥 ${item.calories_burned} kkal</span>
              <div class="flex items-center gap-1.5">
                <button 
                  onclick="app.resumePendingWorkout('${item.pending_id}')"
                  class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold flex items-center gap-1 shadow-sm transition-colors"
                >
                  <i data-lucide="play" class="w-3 h-3 fill-white"></i>
                  <span>Lanjutkan</span>
                </button>
                <button 
                  onclick="app.restartPendingWorkout('${item.pending_id}')"
                  class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-semibold flex items-center gap-1 transition-colors"
                >
                  <i data-lucide="rotate-ccw" class="w-3 h-3"></i>
                  <span>Mulai Ulang</span>
                </button>
                <button 
                  onclick="app.deletePendingWorkout('${item.pending_id}')"
                  class="p-1 rounded-lg bg-slate-800 hover:bg-red-950/60 text-slate-400 hover:text-red-400 text-[11px] transition-colors"
                  title="Hapus"
                >
                  <i data-lucide="trash-2" class="w-3 h-3"></i>
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');

      if (window.lucide) window.lucide.createIcons();
    } catch (e) {
      console.error(e);
    }
  }

  async resumePendingWorkout(pendingId) {
    try {
      const res = await fetch('/api/pending_workouts');
      const list = await res.json();
      const item = list.find(p => p.pending_id === pendingId);
      if (!item) throw new Error("Data sesi tertunda tidak ditemukan.");

      const rRes = await fetch(`/api/routines/${item.routine_id}`);
      if (!rRes.ok) throw new Error("Program latihan tidak ditemukan.");
      const routine = await rRes.json();

      await fetch(`/api/pending_workouts/${pendingId}`, { method: 'DELETE' });

      this.selectedRoutine = routine;
      this.workout.active = true;
      this.workout.paused = false;
      this.workout.routine = routine;
      this.workout.steps = [...routine.steps];
      this.workout.currentStepIndex = Math.min(item.current_step_index || 0, routine.steps.length - 1);
      this.workout.totalElapsedSeconds = item.duration_spent_seconds || 0;
      this.workout.caloriesBurned = item.calories_burned || 0.0;
      this.workout.completedStepsCount = item.current_step_index || 0;

      this.setupCurrentStep();
      this._doNavigate('active-workout');
      this.startWorkoutTimer();

      this.showToast(`Melanjutkan ${routine.title} dari Langkah ${this.workout.currentStepIndex + 1}!`, "info");
      this.audio.playGo();
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  async restartPendingWorkout(pendingId) {
    try {
      const res = await fetch('/api/pending_workouts');
      const list = await res.json();
      const item = list.find(p => p.pending_id === pendingId);
      if (!item) throw new Error("Data sesi tertunda tidak ditemukan.");

      await fetch(`/api/pending_workouts/${pendingId}`, { method: 'DELETE' });

      await this.openRoutineDetail(item.routine_id);
      this.startActiveWorkout();
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  async deletePendingWorkout(pendingId) {
    try {
      await fetch(`/api/pending_workouts/${pendingId}`, { method: 'DELETE' });
      this.showToast("Pelatihan tertunda dihapus.", "info");
      await this.renderPendingWorkouts();
      await this.renderHomePendingBanner();
    } catch (e) {
      this.showToast("Gagal menghapus.", "error");
    }
  }

  // ==========================================================================
  // VIEW 5: LAPORAN (REPORTS, BMI & HISTORY LIST)
  // ==========================================================================
  async renderReportView() {
    try {
      const [statsRes, historyRes] = await Promise.all([
        fetch('/api/stats').then(r => r.json()),
        fetch('/api/history').then(r => r.json())
      ]);

      this.stats = statsRes;

      // 1. Streak & PB
      document.getElementById('report-streak').innerText = `🔥 ${statsRes.streak_days}`;
      document.getElementById('report-pb').innerText = `🏆 ${statsRes.personal_best_streak} Hari`;

      // 2. Weight
      document.getElementById('report-weight').innerText = statsRes.weight_kg.toFixed(1);

      // 3. BMI
      document.getElementById('report-bmi-val').innerText = statsRes.bmi.toFixed(1);
      document.getElementById('report-bmi-cat').innerText = `● ${statsRes.bmi_category}`;
      document.getElementById('report-bmi-cat').style.color = statsRes.bmi_color;
      document.getElementById('report-height-info').innerText = `Tinggi: ${statsRes.height_cm.toFixed(0)} cm`;

      // 4. Lifetime Stats
      document.getElementById('report-total-workouts').innerText = `${statsRes.total_workouts} Sesi`;
      document.getElementById('report-total-calories').innerText = `${statsRes.total_calories} kkal`;
      document.getElementById('report-total-minutes').innerText = `${statsRes.total_minutes} Menit`;

      // 5. Konsistensi Penyelesaian Latihan (Berbasis Jadwal Mingguan)
      const consist = statsRes.consistency || { percentage: 100, scheduled_up_to_today: 0, completed_this_week: 0, missed_count: 0, total_scheduled_week: 5 };
      const consistPct = Math.round(consist.percentage);
      document.getElementById('report-consistency-pct').innerText = `${consistPct}%`;
      const barEl = document.getElementById('report-consistency-bar');
      barEl.style.width = `${Math.max(5, consistPct)}%`;

      if (consistPct >= 70) barEl.className = "bg-emerald-500 h-3 rounded-full transition-all duration-500";
      else if (consistPct >= 40) barEl.className = "bg-amber-500 h-3 rounded-full transition-all duration-500";
      else barEl.className = "bg-red-500 h-3 rounded-full transition-all duration-500";

      document.getElementById('report-consistency-completed').innerText = `✅ ${consist.completed_this_week}/${consist.scheduled_up_to_today} Jadwal Selesai`;
      document.getElementById('report-consistency-missed').innerText = `⚠️ ${consist.missed_count} Terlewat`;
      document.getElementById('report-consistency-total').innerText = `🎯 Target: ${consist.total_scheduled_week ?? 0} Hari/Mgg`;

      // 6. Pelatihan Tertunda (Incomplete Workouts)
      await this.renderPendingWorkouts();

      // 7. History List
      const historyListEl = document.getElementById('history-log-list');
      document.getElementById('report-history-count').innerText = historyRes.length;

      if (historyRes.length === 0) {
        historyListEl.innerHTML = `
          <div class="py-8 text-center text-slate-500 text-xs">
            Belum ada riwayat latihan. Yuk mulai sesi pertama Anda! 💪
          </div>
        `;
      } else {
        historyListEl.innerHTML = historyRes.map(lg => {
          const isOk = (lg.status === 'COMPLETED');
          const statusIcon = isOk ? "✅" : "⚠️";
          const statusColor = isOk ? "text-emerald-400" : "text-amber-400";
          const progColor = isOk ? "bg-emerald-500" : "bg-amber-500";
          
          let dateStr = lg.timestamp;
          try {
            const d = new Date(lg.timestamp);
            dateStr = d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
          } catch (e) {}

          let compPct = 0;
          if (lg.status === 'COMPLETED') {
            compPct = 100;
          } else if (lg.completion_percentage !== undefined && lg.completion_percentage !== null) {
            compPct = Math.round(lg.completion_percentage);
          } else if (lg.total_steps_count > 0) {
            compPct = Math.round((lg.completed_steps_count / lg.total_steps_count) * 100);
          }
          const durMin = Math.round(lg.duration_spent_seconds / 60);

          return `
            <div class="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5 space-y-2">
              <div class="flex items-center justify-between text-xs font-bold">
                <span class="${statusColor} flex items-center gap-1.5">
                  <span>${statusIcon}</span>
                  <span>${lg.routine_title}</span>
                </span>
                <span class="text-slate-400 text-[11px] font-normal">${dateStr}</span>
              </div>

              <!-- Mini Progress Bar -->
              <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div class="${progColor} h-1.5 rounded-full" style="width: ${compPct}%;"></div>
              </div>

              <div class="flex items-center justify-between text-[11px] text-slate-400">
                <span>Tuntas: ${compPct}% • ${durMin} menit • 🔥 ${lg.calories_burned} kkal</span>
                <span class="uppercase font-bold text-[10px] ${statusColor}">${lg.status}</span>
              </div>
            </div>
          `;
        }).join('');
      }

    } catch (e) {
      console.error(e);
      this.showToast("Gagal memuat laporan data.", "error");
    }
  }

  // ==========================================================================
  // VIEW 6: SETTINGS & PREFERENCES
  // ==========================================================================
  renderSettingsView() {
    if (!this.profile) return;
    document.getElementById('setting-name').value = this.profile.name || '';
    if (document.getElementById('setting-age')) document.getElementById('setting-age').value = this.profile.age || 22;
    if (document.getElementById('setting-gender')) document.getElementById('setting-gender').value = this.profile.gender || 'pria';
    document.getElementById('setting-weight').value = this.profile.weight_kg || 65.0;
    document.getElementById('setting-height').value = this.profile.height_cm || 170.0;
    document.getElementById('setting-fitness-level').value = this.profile.fitness_level || 'Beginner';
    if (document.getElementById('setting-target-focus')) document.getElementById('setting-target-focus').value = this.profile.target_focus || 'Full Body';

    document.getElementById('setting-rest-slider').value = this.profile.default_rest_seconds || 15;
    document.getElementById('setting-rest-val').innerText = `${this.profile.default_rest_seconds || 15} Detik`;

    document.getElementById('setting-sound-toggle').checked = Boolean(this.profile.sound_enabled);
    document.getElementById('setting-voice-toggle').checked = Boolean(this.profile.voice_cues_enabled);

    // Sync Onboarding Guide startup toggle
    const hideGuide = localStorage.getItem('fitpulse_hide_guide') === 'true';
    const profileShowGuide = this.profile ? (this.profile.show_onboarding_guide !== false) : true;
    const guideToggle = document.getElementById('setting-guide-startup-toggle');
    if (guideToggle) {
      guideToggle.checked = !hideGuide && profileShowGuide;
    }
  }

  async saveProfileSettings() {
    const name = document.getElementById('setting-name').value.trim();
    const age = parseInt(document.getElementById('setting-age')?.value) || 22;
    const gender = document.getElementById('setting-gender')?.value || 'pria';
    const weight_kg = parseFloat(document.getElementById('setting-weight').value);
    const height_cm = parseFloat(document.getElementById('setting-height').value);
    const fitness_level = document.getElementById('setting-fitness-level').value;
    const target_focus = document.getElementById('setting-target-focus')?.value || 'Full Body';

    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, age, gender, weight_kg, height_cm, fitness_level, target_focus, is_profile_completed: true })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal menyimpan");

      this.profile = data.profile;
      this.showToast("Profil berhasil diperbarui! 🎉", "success");
      await this.loadInitialData();
      this.updateAuthUI();
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  async saveWorkoutPreferences() {
    const default_rest_seconds = parseInt(document.getElementById('setting-rest-slider').value);
    const sound_enabled = document.getElementById('setting-sound-toggle').checked;
    const voice_cues_enabled = document.getElementById('setting-voice-toggle').checked;

    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ default_rest_seconds, sound_enabled, voice_cues_enabled })
      });
      const data = await res.json();
      this.profile = data.profile;
      this.audio.soundEnabled = sound_enabled;
      this.audio.voiceEnabled = voice_cues_enabled;

      this.showToast("Preferensi latihan tersimpan!", "success");
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  // ==========================================================================
  // MODAL 1: EXERCISE GUIDE & MUSCLE ANATOMY ("📖 Panduan Gerakan")
  // ==========================================================================
  async openExerciseGuideModal(exerciseId) {
    try {
      const res = await fetch(`/api/exercises/${exerciseId}`);
      if (!res.ok) throw new Error("Gerakan tidak ditemukan");
      const ex = await res.json();

      document.getElementById('guide-title').innerText = ex.name;
      document.getElementById('guide-desc').innerText = ex.accessible_description || "Panduan postur dan teknik pelaksanaan yang aman.";
      document.getElementById('guide-muscle-badge').innerText = ex.target_muscle.toUpperCase();
      document.getElementById('guide-diff-badge').innerText = ex.difficulty;

      // 1:1 Image
      const imgPath = "/" + (ex.image_path || ("workout_data/images/" + ex.id + ".png")).replace(/\\/g, '/');
      const guideImgEl = document.getElementById('guide-image');
      if (guideImgEl) {
        guideImgEl.src = imgPath;
        guideImgEl.onerror = function() {
          this.onerror = null;
          this.src = "/workout_data/images/ex_jumping_jacks.png";
        };
      }

      // Dynamic Anatomy Diagram from server
      document.getElementById('guide-anatomy-img').src = `/api/exercises/${ex.id}/anatomy?t=${Date.now()}`;
      document.getElementById('guide-focus-areas').innerText = ex.focus_areas && ex.focus_areas.length ? ex.focus_areas.join(', ') : ex.target_muscle;

      // Mistakes
      const mistakesList = document.getElementById('guide-mistakes-list');
      if (ex.common_mistakes && ex.common_mistakes.length > 0) {
        mistakesList.innerHTML = ex.common_mistakes.map((m, idx) => `
          <div class="bg-red-950/20 border border-red-900/30 rounded-xl p-3 space-y-0.5">
            <span class="font-bold text-red-400 block">${idx + 1}. ${m.title}</span>
            <p class="text-slate-300 text-[11px] leading-relaxed">${m.desc}</p>
          </div>
        `).join('');
      } else {
        mistakesList.innerHTML = `<p class="text-slate-500 text-xs">Jaga punggung tetap lurus dan kendalikan ritme gerakan.</p>`;
      }

      // Breathing Tips
      const breathList = document.getElementById('guide-breathing-tips');
      if (ex.breathing_tips && ex.breathing_tips.length > 0) {
        breathList.innerHTML = ex.breathing_tips.map(t => `<p>• ${t}</p>`).join('');
      } else {
        breathList.innerHTML = `<p>• Buang napas saat fase kontraksi (mengangkat), tarik napas saat fase relaksasi.</p>`;
      }

      // Instructions
      const instList = document.getElementById('guide-instructions-list');
      if (ex.instructions && ex.instructions.length > 0) {
        instList.innerHTML = ex.instructions.map(inst => `<li>${inst}</li>`).join('');
      } else {
        instList.innerHTML = `<li>Lakukan gerakan dengan perlahan dan perhatikan form yang benar.</li>`;
      }

      this.openModal('modal-exercise-guide');
    } catch (e) {
      console.error(e);
      this.showToast("Gagal memuat panduan gerakan.", "error");
    }
  }

  openCurrentExerciseGuide() {
    const cur = this.getCurrentStep();
    const next = this.getNextStep();
    if (cur && cur.exercise) {
      this.openExerciseGuideModal(cur.exercise.id);
    } else if (cur && cur.step_type === 'Rest' && next && next.exercise) {
      this.openExerciseGuideModal(next.exercise.id);
    }
  }

  // ==========================================================================
  // MODAL 2: ROUTINE PLAN EDITOR & TEMPLATE MANAGEMENT
  // ==========================================================================
  openRoutinePlanEditor() {
    if (!this.selectedRoutine) return;

    // Deep clone steps for local editing
    this.editingRoutineSteps = JSON.parse(JSON.stringify(this.selectedRoutine.steps || []));

    // Populate title
    const titleInput = document.getElementById('plan-editor-title-input');
    if (titleInput) titleInput.value = this.selectedRoutine.title || '';

    // Hide add drawer
    const drawer = document.getElementById('plan-editor-add-drawer');
    if (drawer) drawer.classList.add('hidden');

    // Populate exercise picker dropdown
    const picker = document.getElementById('plan-editor-exercise-picker');
    if (picker && this.exercises && this.exercises.length > 0) {
      picker.innerHTML = this.exercises.map(ex => `
        <option value="${ex.id}">${ex.name} (${ex.target_muscle} • ${ex.difficulty})</option>
      `).join('');
    }

    this.renderPlanEditorSteps();
    this.openModal('modal-plan-editor');
  }

  renderPlanEditorSteps() {
    const badge = document.getElementById('plan-editor-count-badge');
    if (badge) badge.innerText = `${this.editingRoutineSteps ? this.editingRoutineSteps.length : 0} langkah`;

    const container = document.getElementById('plan-editor-steps-list');
    if (!container) return;

    if (!this.editingRoutineSteps || this.editingRoutineSteps.length === 0) {
      container.innerHTML = `
        <div class="text-center py-8 text-slate-500 text-xs border border-dashed border-slate-800 rounded-2xl">
          Belum ada gerakan dalam template ini.<br/>
          Klik <strong>+ Tambah Gerakan</strong> atau <strong>+ Istirahat</strong> untuk memulai.
        </div>
      `;
      return;
    }

    const totalSteps = this.editingRoutineSteps.length;
    container.innerHTML = this.editingRoutineSteps.map((st, idx) => {
      const isRest = st.step_type === 'Rest' || (typeof st.step_type === 'string' && st.step_type.toLowerCase() === 'rest');
      const isEx = !isRest;
      const exObj = st.exercise || (st.exercise_id ? this.exercises.find(e => e.id === st.exercise_id) : null);
      const title = isRest ? 'Istirahat (Rest)' : (exObj ? exObj.name : 'Gerakan Latihan');
      const subtitle = isRest ? 'Fase Pemulihan' : (exObj ? `${exObj.target_muscle} • ${exObj.difficulty}` : 'Latihan Fisik');
      const isRep = Boolean(st.target_reps || (exObj && exObj.is_reps_based));
      const valueLabel = isRep ? `×${st.target_reps || 12}` : `${st.duration_seconds || 30}s`;

      return `
        <div class="bg-slate-950 border ${isRest ? 'border-sky-900/40' : 'border-slate-800'} rounded-2xl p-3 flex items-center justify-between gap-2.5 transition-all">
          <div class="flex items-center gap-1.5 text-slate-500">
            <button 
              type="button"
              onclick="app.planEditorMoveStep(${idx}, -1)" 
              ${idx === 0 ? 'disabled' : ''}
              class="w-6 h-6 rounded flex items-center justify-center hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-20 disabled:hover:bg-transparent text-xs"
              title="Pindah ke atas"
            >▲</button>
            <button 
              type="button"
              onclick="app.planEditorMoveStep(${idx}, 1)" 
              ${idx === totalSteps - 1 ? 'disabled' : ''}
              class="w-6 h-6 rounded flex items-center justify-center hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-20 disabled:hover:bg-transparent text-xs"
              title="Pindah ke bawah"
            >▼</button>
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold ${isRest ? 'text-sky-300' : 'text-white'} truncate">${idx + 1}. ${title}</span>
              ${isRest ? '<span class="text-[9px] px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-400 font-semibold">REST</span>' : ''}
            </div>
            <span class="text-[11px] text-slate-400 block truncate">${subtitle}</span>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <button 
              type="button"
              onclick="app.planEditorAdjustStep(${idx}, -1)"
              class="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold flex items-center justify-center text-xs"
              title="Kurangi"
            >-</button>
            <span class="w-14 text-center font-mono font-bold text-xs ${isRest ? 'text-sky-400' : 'text-brand-400'}">
              ${valueLabel}
            </span>
            <button 
              type="button"
              onclick="app.planEditorAdjustStep(${idx}, 1)"
              class="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold flex items-center justify-center text-xs"
              title="Tambah"
            >+</button>
            <button 
              type="button"
              onclick="app.planEditorRemoveStep(${idx})"
              class="w-7 h-7 rounded-lg bg-red-500/10 hover:bg-red-500/30 text-red-400 font-bold flex items-center justify-center text-xs ml-1 transition-colors"
              title="Hapus langkah ini"
            >✕</button>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  }

  planEditorAdjustStep(idx, direction) {
    if (!this.editingRoutineSteps || !this.editingRoutineSteps[idx]) return;
    const step = this.editingRoutineSteps[idx];
    const isRest = step.step_type === 'Rest' || (typeof step.step_type === 'string' && step.step_type.toLowerCase() === 'rest');
    const exObj = step.exercise || (step.exercise_id ? this.exercises.find(e => e.id === step.exercise_id) : null);
    const isRep = !isRest && Boolean(step.target_reps || (exObj && exObj.is_reps_based));

    if (isRep) {
      step.target_reps = Math.max(1, (step.target_reps || 12) + (direction * 2));
    } else {
      step.duration_seconds = Math.max(5, (step.duration_seconds || 30) + (direction * 5));
    }

    this.renderPlanEditorSteps();
  }

  planEditorMoveStep(idx, direction) {
    if (!this.editingRoutineSteps) return;
    const targetIdx = idx + direction;
    if (targetIdx < 0 || targetIdx >= this.editingRoutineSteps.length) return;

    const temp = this.editingRoutineSteps[idx];
    this.editingRoutineSteps[idx] = this.editingRoutineSteps[targetIdx];
    this.editingRoutineSteps[targetIdx] = temp;
    this.renderPlanEditorSteps();
  }

  planEditorRemoveStep(idx) {
    if (!this.editingRoutineSteps || idx < 0 || idx >= this.editingRoutineSteps.length) return;
    this.editingRoutineSteps.splice(idx, 1);
    this.renderPlanEditorSteps();
  }

  planEditorOpenAddExerciseDialog() {
    const drawer = document.getElementById('plan-editor-add-drawer');
    if (drawer) {
      drawer.classList.toggle('hidden');
    }
  }

  planEditorAddRestStep() {
    if (!this.editingRoutineSteps) this.editingRoutineSteps = [];
    this.editingRoutineSteps.push({
      step_id: `step_rest_${Date.now()}`,
      step_type: 'Rest',
      duration_seconds: 30,
      exercise: null,
      exercise_id: null,
      target_reps: null
    });
    this.renderPlanEditorSteps();
    this.showToast("+ Istirahat 30s ditambahkan", "info");
  }

  planEditorConfirmAddExercise() {
    const picker = document.getElementById('plan-editor-exercise-picker');
    const exId = picker ? picker.value : null;
    if (!exId) return;

    const ex = this.exercises.find(e => e.id === exId);
    if (!ex) return;

    if (!this.editingRoutineSteps) this.editingRoutineSteps = [];
    this.editingRoutineSteps.push({
      step_id: `step_ex_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      step_type: 'Exercise',
      exercise_id: ex.id,
      exercise: ex,
      duration_seconds: ex.default_duration_seconds || 30,
      target_reps: ex.is_reps_based ? (ex.default_reps || 12) : null
    });

    const drawer = document.getElementById('plan-editor-add-drawer');
    if (drawer) drawer.classList.add('hidden');

    this.renderPlanEditorSteps();
    this.showToast(`Gerakan ${ex.name} ditambahkan ke template!`, "success");
  }

  async savePlanEditorChanges() {
    if (!this.selectedRoutine || !this.editingRoutineSteps) return;

    const hasExercise = this.editingRoutineSteps.some(
      s => s.step_type === 'Exercise' || (typeof s.step_type === 'string' && s.step_type.toLowerCase() === 'exercise')
    );
    if (!hasExercise) {
      this.showToast("Template harus memiliki minimal 1 gerakan latihan.", "error");
      return;
    }

    const titleInput = document.getElementById('plan-editor-title-input');
    const newTitle = titleInput ? titleInput.value.trim() : '';

    const payload = {
      title: newTitle || this.selectedRoutine.title,
      description: this.selectedRoutine.description,
      steps: this.editingRoutineSteps.map(s => {
        const isRest = s.step_type === 'Rest' || (typeof s.step_type === 'string' && s.step_type.toLowerCase() === 'rest');
        const exId = s.exercise ? s.exercise.id : (s.exercise_id || null);
        return {
          step_id: s.step_id,
          step_type: isRest ? 'Rest' : 'Exercise',
          exercise_id: isRest ? null : exId,
          duration_seconds: s.duration_seconds || 30,
          target_reps: s.target_reps || null
        };
      })
    };

    try {
      const res = await fetch(`/api/routines/${this.selectedRoutine.id}/steps`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal menyimpan perubahan template.");

      this.selectedRoutine = data.routine;
      this.closeModal('modal-plan-editor');
      await this.openRoutineDetail(this.selectedRoutine.id);
      await this.loadInitialData(); // Refresh list routines and banners
      this.showToast("Perubahan template berhasil disimpan!", "success");
    } catch (e) {
      this.showToast(e.message || "Gagal menyimpan rencana latihan.", "error");
    }
  }

  // ==========================================================================
  // ROUTINE TEMPLATE DELETION
  // ==========================================================================
  promptDeleteRoutine() {
    if (!this.selectedRoutine) return;
    const textEl = document.getElementById('delete-routine-confirm-text');
    if (textEl) {
      textEl.innerText = `Apakah Anda yakin ingin menghapus template "${this.selectedRoutine.title}"? Seluruh langkah dalam template ini akan dihapus.`;
    }
    this.openModal('modal-delete-routine');
  }

  async executeDeleteRoutine() {
    if (!this.selectedRoutine) return;
    const routineId = this.selectedRoutine.id;

    try {
      const res = await fetch(`/api/routines/${routineId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal menghapus template latihan.");

      this.closeModal('modal-delete-routine');
      this.selectedRoutine = null;
    this.editingRoutineSteps = [];
      this.showToast(data.message || "Template berhasil dihapus!", "success");
      await this.loadInitialData();
      this.navigate('training');
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  // ==========================================================================
  // MODAL 3: WEEKLY SCHEDULE PLANNER
  // ==========================================================================
  async openScheduleModal() {
    try {
      const sched = await fetch('/api/schedule').then(r => r.json());
      this.schedule = sched;

      const dayOrder = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];
      const container = document.getElementById('schedule-days-container');

      const routineOptions = this.routines.map(r => `<option value="${r.id}">${r.title}</option>`).join('');

      container.innerHTML = dayOrder.map(day => {
        const item = sched.days[day] || { is_rest_day: false, routine_id: "" };
        const isRest = Boolean(item.is_rest_day);

        return `
          <div id="sched-row-${day}" class="bg-slate-950 border ${isRest ? 'border-sky-900/30 bg-slate-950/70' : 'border-slate-800'} rounded-2xl p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all">
            <div class="flex items-center justify-between sm:justify-start gap-2 sm:w-28">
              <span class="font-bold text-xs sm:text-sm text-white">${day}</span>
              <span id="sched-tag-${day}" class="text-[10px] px-2 py-0.5 rounded-full font-bold ${isRest ? 'bg-sky-500/20 text-sky-400' : 'bg-brand-500/20 text-brand-400'}">
                ${isRest ? 'Istirahat' : 'Latihan'}
              </span>
            </div>

            <div class="flex items-center gap-2.5 flex-1">
              <select 
                id="sched-sel-${day}" 
                class="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500 disabled:opacity-40 disabled:cursor-not-allowed"
                ${isRest ? 'disabled' : ''}
              >
                ${routineOptions}
              </select>

              <label class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 cursor-pointer hover:border-slate-700 select-none transition-colors shrink-0">
                <input 
                  type="checkbox" 
                  id="sched-rest-${day}" 
                  ${isRest ? 'checked' : ''} 
                  onchange="app.onScheduleRestToggled('${day}')"
                  class="rounded bg-slate-800 border-slate-700 accent-sky-500 cursor-pointer w-4 h-4"
                />
                <span class="text-xs font-semibold">Istirahat</span>
              </label>
            </div>
          </div>
        `;
      }).join('');

      // Set initial values
      dayOrder.forEach(day => {
        const item = sched.days[day];
        if (item && item.routine_id) {
          const sel = document.getElementById(`sched-sel-${day}`);
          if (sel) sel.value = item.routine_id;
        }
      });

      this.updateScheduleModalBadge();
      this.openModal('modal-schedule-planner');
    } catch (e) {
      console.error(e);
      this.showToast("Gagal memuat jadwal mingguan.", "error");
    }
  }

  onScheduleRestToggled(day) {
    const isRest = document.getElementById(`sched-rest-${day}`).checked;
    const sel = document.getElementById(`sched-sel-${day}`);
    const tag = document.getElementById(`sched-tag-${day}`);
    const row = document.getElementById(`sched-row-${day}`);

    if (sel) sel.disabled = isRest;
    if (tag) {
      tag.innerText = isRest ? 'Istirahat' : 'Latihan';
      tag.className = `text-[10px] px-2 py-0.5 rounded-full font-bold ${isRest ? 'bg-sky-500/20 text-sky-400' : 'bg-brand-500/20 text-brand-400'}`;
    }
    if (row) {
      if (isRest) {
        row.className = "bg-slate-950 border border-sky-900/30 bg-slate-950/70 rounded-2xl p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all";
      } else {
        row.className = "bg-slate-950 border border-slate-800 rounded-2xl p-3 sm:p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all";
      }
    }
    this.updateScheduleModalBadge();
  }

  updateScheduleModalBadge() {
    const dayOrder = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];
    let workoutCount = 0;
    let restCount = 0;

    dayOrder.forEach(day => {
      const chk = document.getElementById(`sched-rest-${day}`);
      if (chk && chk.checked) restCount++;
      else workoutCount++;
    });

    const badge = document.getElementById('schedule-target-count-badge');
    if (badge) {
      badge.innerText = `🎯 Target: ${workoutCount} Hari Latihan • 💤 ${restCount} Hari Istirahat`;
    }
  }

  async saveAllScheduleDays() {
    const btn = document.getElementById('btn-save-all-schedule');
    const oldHtml = btn ? btn.innerHTML : '';
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span>Menyimpan...</span>`;
    }

    const dayOrder = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"];
    const bulkPayload = {};

    dayOrder.forEach(day => {
      const restEl = document.getElementById(`sched-rest-${day}`);
      const selEl = document.getElementById(`sched-sel-${day}`);
      const isRest = restEl ? restEl.checked : false;
      const routineId = selEl ? selEl.value : null;

      bulkPayload[day] = {
        is_rest_day: isRest,
        routine_id: isRest ? null : routineId,
        scheduled_time: "07:00",
        reminder_enabled: true
      };
    });

    try {
      const res = await fetch('/api/schedule/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bulkPayload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal menyimpan jadwal mingguan");

      this.schedule = data.schedule;
      this.closeModal('modal-schedule-planner');
      await this.loadInitialData();
      this.renderTodayActivity();
      this.setupWeeklyDots();
      this.showToast("Seluruh jadwal mingguan berhasil disimpan! 🎯", "success");
    } catch (e) {
      this.showToast(e.message || "Gagal menyimpan jadwal mingguan.", "error");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = oldHtml;
      }
    }
  }

  // ==========================================================================
  // MODAL 4: CUSTOM ROUTINE TEMPLATE BUILDER
  // ==========================================================================
  openCustomBuilderModal() {
    const list = document.getElementById('builder-exercises-list');
    list.innerHTML = this.exercises.map(ex => `
      <label class="flex items-center gap-2.5 text-xs text-slate-200 cursor-pointer p-1.5 hover:bg-slate-900 rounded-lg">
        <input type="checkbox" value="${ex.id}" class="builder-ex-check rounded bg-slate-900 border-slate-700 accent-brand-500" />
        <span class="font-bold flex-1 truncate">${ex.name}</span>
        <span class="text-slate-500 text-[11px]">${ex.target_muscle}</span>
      </label>
    `).join('');

    this.openModal('modal-custom-builder');
  }

  async saveCustomRoutine() {
    const title = document.getElementById('builder-title').value.trim();
    const desc = document.getElementById('builder-desc').value.trim();
    const muscle = document.getElementById('builder-muscle').value;
    const diff = document.getElementById('builder-diff').value;

    const checkedBoxes = Array.from(document.querySelectorAll('.builder-ex-check:checked'));
    const selectedIds = checkedBoxes.map(cb => cb.value);

    if (!title) {
      this.showToast("Judul rutinitas tidak boleh kosong.", "error");
      return;
    }
    if (selectedIds.length === 0) {
      this.showToast("Pilih minimal 1 gerakan latihan.", "error");
      return;
    }

    try {
      const res = await fetch('/api/routines/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description: desc || "Kombinasi latihan kustom personal.",
          target_muscle: muscle,
          difficulty: diff,
          selected_exercise_ids: selectedIds
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal membuat template");

      this.closeModal('modal-custom-builder');
      this.showToast("Rutinitas kustom berhasil dibuat! 🎉", "success");
      await this.loadInitialData();
      this.openRoutineDetail(data.routine.id);
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  // ==========================================================================
  // QUICK DIALOGS (WEIGHT / HEIGHT)
  // ==========================================================================
  openWeightLoggerModal() {
    document.getElementById('prompt-modal-title').innerText = "Catat Berat Badan Baru";
    document.getElementById('prompt-modal-desc').innerText = "Masukkan berat badan Anda dalam kilogram (kg):";
    const inp = document.getElementById('prompt-modal-input');
    inp.value = this.profile?.weight_kg || 65.0;

    document.getElementById('btn-prompt-confirm').onclick = async () => {
      const val = parseFloat(inp.value);
      if (isNaN(val) || val <= 20 || val > 300) {
        this.showToast("Berat badan harus antara 20 - 300 kg.", "error");
        return;
      }
      await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ weight_kg: val })
      });
      this.closeModal('modal-quick-prompt');
      this.showToast("Berat badan berhasil dicatat!", "success");
      await this.loadInitialData();
      this.renderReportView();
    };

    this.openModal('modal-quick-prompt');
  }

  openHeightLoggerModal() {
    document.getElementById('prompt-modal-title').innerText = "Ubah Tinggi Badan";
    document.getElementById('prompt-modal-desc').innerText = "Masukkan tinggi badan Anda dalam centimeter (cm):";
    const inp = document.getElementById('prompt-modal-input');
    inp.value = this.profile?.height_cm || 170.0;

    document.getElementById('btn-prompt-confirm').onclick = async () => {
      const val = parseFloat(inp.value);
      if (isNaN(val) || val <= 50 || val > 260) {
        this.showToast("Tinggi badan harus antara 50 - 260 cm.", "error");
        return;
      }
      await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ height_cm: val })
      });
      this.closeModal('modal-quick-prompt');
      this.showToast("Tinggi badan berhasil diperbarui!", "success");
      await this.loadInitialData();
      this.renderReportView();
    };

    this.openModal('modal-quick-prompt');
  }

  // ==========================================================================
  // DEVICE SIMULATOR PREVIEW (HCI EVALUATION FEATURE)
  // ==========================================================================
  toggleDeviceMenu(e) {
    if (e) e.stopPropagation();
    const dropdown = document.getElementById('device-menu-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('hidden');
    }
  }

  setDeviceMode(mode) {
    const wrapper = document.getElementById('device-wrapper');
    const dropdown = document.getElementById('device-menu-dropdown');
    if (dropdown) dropdown.classList.add('hidden');

    if (!wrapper) return;

    wrapper.classList.remove('device-mode-mobile', 'device-mode-tablet', 'device-mode-desktop');

    // Update checkmarks
    ['responsive', 'desktop', 'tablet', 'mobile'].forEach(m => {
      const check = document.getElementById(`check-mode-${m}`);
      if (check) {
        if (m === mode) check.classList.remove('hidden');
        else check.classList.add('hidden');
      }
    });

    const label = document.getElementById('device-mode-label');

    if (mode === 'mobile') {
      wrapper.classList.add('device-mode-mobile');
      if (label) label.innerText = "Mode: Mobile";
      this.showToast("Beralih ke mode simulasi Mobile (420px)", "info");
    } else if (mode === 'tablet') {
      wrapper.classList.add('device-mode-tablet');
      if (label) label.innerText = "Mode: Tablet";
      this.showToast("Beralih ke mode simulasi Tablet (768px)", "info");
    } else if (mode === 'desktop') {
      wrapper.classList.add('device-mode-desktop');
      if (label) label.innerText = "Mode: Desktop";
      this.showToast("Beralih ke mode simulasi Desktop (1080px)", "info");
    } else {
      if (label) label.innerText = "Mode Device";
      this.showToast("Beralih ke mode Fluid Responsive Penuh", "info");
    }
  }

  // ==========================================================================
  // AUDIO & VOICE CUSTOMIZATION SETTINGS
  // ==========================================================================
  initAudioVoicesUI() {
    this.updateVoiceModeButtons();
    this.populateVoiceSelect();

    const pitchSlider = document.getElementById('setting-pitch-slider');
    const pitchVal = document.getElementById('setting-pitch-val');
    if (pitchSlider && pitchVal) {
      pitchSlider.value = this.audio.pitch;
      pitchVal.innerText = `${this.audio.pitch.toFixed(1)}x`;
    }

    const rateSlider = document.getElementById('setting-rate-slider');
    const rateVal = document.getElementById('setting-rate-val');
    if (rateSlider && rateVal) {
      rateSlider.value = this.audio.rate;
      rateVal.innerText = `${this.audio.rate.toFixed(1)}x`;
    }
  }

  setVoiceMode(mode) {
    this.audio.voiceMode = mode;
    this.audio.saveSettings();
    this.updateVoiceModeButtons();
    if (mode === 'chime') {
      this.showToast("Mode Nada Akustik aktif: Melodi instrumen dinamis (100% tanpa suara Google).", "info");
      this.audio.playExerciseStartChime();
    } else {
      this.showToast("Mode Suara Vokal (TTS) aktif.", "info");
      this.audio.speak("Mode suara vokal aktif.");
    }
  }

  updateVoiceModeButtons() {
    const chimeBtn = document.getElementById('voice-mode-chime-btn');
    const voiceBtn = document.getElementById('voice-mode-voice-btn');
    const dropContainer = document.getElementById('voice-dropdown-container');
    const slidersContainer = document.getElementById('voice-sliders-container');

    const isChime = (this.audio.voiceMode === 'chime');

    if (chimeBtn && voiceBtn) {
      if (isChime) {
        chimeBtn.className = "p-3.5 rounded-xl border text-left transition-all bg-brand-500/15 border-brand-500 ring-1 ring-brand-500 shadow-md";
        voiceBtn.className = "p-3.5 rounded-xl border text-left transition-all bg-slate-950 border-slate-800 hover:border-slate-700 opacity-60";
      } else {
        voiceBtn.className = "p-3.5 rounded-xl border text-left transition-all bg-brand-500/15 border-brand-500 ring-1 ring-brand-500 shadow-md";
        chimeBtn.className = "p-3.5 rounded-xl border text-left transition-all bg-slate-950 border-slate-800 hover:border-slate-700 opacity-60";
      }
    }

    if (dropContainer) {
      dropContainer.style.display = isChime ? 'none' : 'block';
    }
    if (slidersContainer) {
      slidersContainer.style.display = isChime ? 'none' : 'grid';
    }
  }

  populateVoiceSelect() {
    const select = document.getElementById('setting-voice-select');
    const hint = document.getElementById('voice-count-hint');
    if (!select || !window.speechSynthesis) return;

    let voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) {
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => this.populateVoiceSelect();
      }
      return;
    }

    this.audio.availableVoices = voices;
    if (hint) hint.innerText = `${voices.length} karakter suara terpasang`;

    select.innerHTML = '';

    const indonesianVoices = voices.filter(v => v.lang.startsWith('id'));
    const englishVoices = voices.filter(v => v.lang.startsWith('en'));
    const otherVoices = voices.filter(v => !v.lang.startsWith('id') && !v.lang.startsWith('en'));

    const addGroup = (label, list) => {
      if (list.length === 0) return;
      const optGroup = document.createElement('optgroup');
      optGroup.label = label;
      list.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.voiceURI;
        const isGoogle = v.name.toLowerCase().includes('google');
        const isMicrosoft = v.name.toLowerCase().includes('microsoft') || v.name.toLowerCase().includes('natural');
        const tag = isMicrosoft ? " [Microsoft Natural - Rekomendasi]" : (isGoogle ? " [Google Voice]" : "");
        opt.innerText = `${v.name} (${v.lang})${tag}`;
        if (v.voiceURI === this.audio.selectedVoiceURI) {
          opt.selected = true;
        }
        optGroup.appendChild(opt);
      });
      select.appendChild(optGroup);
    };

    addGroup("🇮🇩 Bahasa Indonesia", indonesianVoices);
    addGroup("🇬🇧 Suara Bahasa Inggris (Jernih & Natural)", englishVoices);
    addGroup("🌐 Suara Bahasa Lainnya", otherVoices);

    if (!this.audio.selectedVoiceURI) {
      const nonGoogle = indonesianVoices.find(v => !v.name.toLowerCase().includes('google')) || indonesianVoices[0];
      if (nonGoogle) {
        this.audio.selectedVoiceURI = nonGoogle.voiceURI;
        select.value = nonGoogle.voiceURI;
        this.audio.saveSettings();
      }
    }
  }

  onVoiceSelectChanged(uri) {
    this.audio.selectedVoiceURI = uri;
    this.audio.saveSettings();
    this.showToast("Karakter suara diperbarui.", "info");
  }

  onPitchChanged(val) {
    this.audio.pitch = parseFloat(val);
    const label = document.getElementById('setting-pitch-val');
    if (label) label.innerText = `${this.audio.pitch.toFixed(1)}x`;
    this.audio.saveSettings();
  }

  onRateChanged(val) {
    this.audio.rate = parseFloat(val);
    const label = document.getElementById('setting-rate-val');
    if (label) label.innerText = `${this.audio.rate.toFixed(1)}x`;
    this.audio.saveSettings();
  }

  testAudioPreview() {
    if (this.audio.voiceMode === 'chime') {
      this.audio.playExerciseStartChime();
      setTimeout(() => {
        this.audio.playRestChime();
      }, 700);
      this.showToast("Memainkan nada instrumen akustik (Mulai & Istirahat)...", "info");
    } else {
      this.audio.speak("Mulai latihan! Ayo tetap konsisten dan bersemangat.");
      this.showToast("Memainkan contoh suara dengan karakter dan nada yang dipilih...", "info");
    }
  }

  // ==========================================================================
  // RESET USER DATA MODAL
  // ==========================================================================
  openResetModal() {
    const input = document.getElementById('reset-confirm-input');
    const btn = document.getElementById('btn-do-reset');
    if (input) input.value = '';
    if (btn) btn.disabled = true;
    this.openModal('modal-reset-confirm');
  }

  onResetInputChanged(val) {
    const btn = document.getElementById('btn-do-reset');
    if (btn) {
      btn.disabled = (val.trim().toLowerCase() !== 'confirm');
    }
  }

  async executeResetData() {
    const input = document.getElementById('reset-confirm-input');
    if (!input || input.value.trim().toLowerCase() !== 'confirm') {
      this.showToast("Ketik 'confirm' untuk mengonfirmasi reset.", "error");
      return;
    }

    try {
      const res = await fetch('/api/reset_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm_text: input.value.trim() })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gagal mereset data");

      this.closeModal('modal-reset-confirm');
      this.showToast("Seluruh data pengguna berhasil direset ke setelan awal! 🗑️", "success");
      await this.loadInitialData();
      await this.renderHomePendingBanner();
      this.navigate('training');
    } catch (e) {
      this.showToast(e.message, "error");
    }
  }

  // ==========================================================================
  // ONBOARDING USER GUIDE OVERLAY (PANDUAN PENGGUNA)
  // ==========================================================================
  openUserGuideOverlay(step = 1) {
    this.guideCurrentStep = step;
    const modal = document.getElementById('modal-user-guide');
    const imgEl = document.getElementById('guide-overlay-img');
    const badgeEl = document.getElementById('guide-step-badge');
    const dot1 = document.getElementById('guide-dot-1');
    const dot2 = document.getElementById('guide-dot-2');
    const actionBtn = document.getElementById('guide-btn-action');
    const checkDontShow = document.getElementById('guide-checkbox-dont-show');

    if (!modal || !imgEl) return;

    if (step === 1) {
      imgEl.src = '/workout_data/images/panduan1.png';
      if (badgeEl) badgeEl.innerText = 'Langkah 1/2';
      if (dot1) {
        dot1.className = 'w-3.5 h-2.5 rounded-full bg-brand-500 transition-all';
      }
      if (dot2) {
        dot2.className = 'w-2 h-2.5 rounded-full bg-slate-700 transition-all';
      }
      if (actionBtn) {
        actionBtn.innerHTML = '<span>Lanjut</span><i data-lucide="chevron-right" class="w-3.5 h-3.5"></i>';
      }
    } else {
      imgEl.src = '/workout_data/images/panduan2.png';
      if (badgeEl) badgeEl.innerText = 'Langkah 2/2';
      if (dot1) {
        dot1.className = 'w-2 h-2.5 rounded-full bg-slate-700 transition-all';
      }
      if (dot2) {
        dot2.className = 'w-3.5 h-2.5 rounded-full bg-brand-500 transition-all';
      }
      if (actionBtn) {
        actionBtn.innerHTML = '<span>Mulai Aplikasi ✓</span>';
      }
    }

    // Synchronize "Jangan tampilkan lagi" checkbox
    const hideGuide = localStorage.getItem('fitpulse_hide_guide') === 'true';
    if (checkDontShow) {
      checkDontShow.checked = hideGuide;
    }

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    if (window.lucide) window.lucide.createIcons();
  }

  advanceUserGuide() {
    if (this.guideCurrentStep === 1) {
      this.openUserGuideOverlay(2);
    } else {
      this.closeUserGuideOverlay();
    }
  }

  closeUserGuideOverlay() {
    const modal = document.getElementById('modal-user-guide');
    if (modal) {
      modal.classList.add('hidden');
      document.body.style.overflow = '';
    }
  }

  onGuideDontShowAgainChanged(isChecked) {
    localStorage.setItem('fitpulse_hide_guide', isChecked ? 'true' : 'false');
    const settingToggle = document.getElementById('setting-guide-startup-toggle');
    if (settingToggle) {
      settingToggle.checked = !isChecked;
    }

    // Background sync to backend profile
    fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ show_onboarding_guide: !isChecked })
    }).catch(e => console.warn("Failed syncing guide preference to profile:", e));

    if (isChecked) {
      this.showToast("Panduan otomatis dinonaktifkan. Anda dapat membukanya kembali dari menu Pengaturan.", "info");
    } else {
      this.showToast("Panduan otomatis diaktifkan saat aplikasi dibuka.", "info");
    }
  }

  toggleGuideStartupFromSettings(isChecked) {
    const hideGuide = !isChecked;
    localStorage.setItem('fitpulse_hide_guide', hideGuide ? 'true' : 'false');
    const checkDontShow = document.getElementById('guide-checkbox-dont-show');
    if (checkDontShow) {
      checkDontShow.checked = hideGuide;
    }

    // Background sync to backend profile
    fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ show_onboarding_guide: isChecked })
    }).catch(e => console.warn("Failed syncing guide preference to profile:", e));

    if (isChecked) {
      this.showToast("Panduan akan otomatis muncul saat aplikasi dibuka.", "success");
    } else {
      this.showToast("Panduan otomatis dinonaktifkan saat aplikasi dibuka.", "info");
    }
  }

  // ==========================================================================
  // MODAL UTILITIES
  // ==========================================================================
  openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) {
      el.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      if (window.lucide) window.lucide.createIcons();
    }
  }

  closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) {
      el.classList.add('hidden');
      document.body.style.overflow = '';
    }
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const bgMap = {
      success: 'bg-emerald-600 text-white',
      error: 'bg-red-600 text-white',
      info: 'bg-slate-800 text-white border border-slate-700'
    };

    const toast = document.createElement('div');
    toast.className = `px-4 py-2.5 rounded-xl shadow-2xl text-xs font-bold transition-all duration-300 transform translate-y-2 opacity-0 flex items-center gap-2 ${bgMap[type] || bgMap.info}`;
    toast.innerHTML = `<span>${message}</span>`;

    container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.remove('translate-y-2', 'opacity-0');
    });

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-2');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// Instantiate global app
window.app = new FitPulseApp();
window.addEventListener('DOMContentLoaded', () => {
  window.app.init();
});

// Close device menu dropdown on click outside
window.addEventListener('click', (e) => {
  const container = document.getElementById('device-menu-container');
  const dropdown = document.getElementById('device-menu-dropdown');
  if (dropdown && container && !container.contains(e.target)) {
    dropdown.classList.add('hidden');
  }
});

