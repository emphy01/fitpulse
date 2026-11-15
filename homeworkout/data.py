"""
Seed and Default Data for Home Workout Library.
Rich in descriptions, accessibility guidance, realistic scientific MET values,
and comprehensive workout templates across muscle groups and difficulty tiers.
"""

from typing import List, Dict
from .models import (
    Exercise, WorkoutStep, WorkoutRoutine, MuscleGroup, DifficultyLevel, StepType,
    DailySchedule, WeeklySchedule, DayOfWeek
)

# Comprehensive Exercise Catalog
DEFAULT_EXERCISES = [
    # ---- FULL BODY ----
    Exercise(
        id="ex_jumping_jacks",
        name="Jumping Jacks",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=8.0,
        equipment_needed="None",
        instructions=[
            "Berdiri tegak dengan kaki rapat dan tangan di samping.",
            "Lompat sedikit sambil membuka kaki selebar bahu dan mengangkat tangan ke atas kepala.",
            "Lompat kembali ke posisi semula secara berirama."
        ],
        accessible_description="Lompatan ritmis membuka tangan dan kaki bersamaan lalu kembali merapat.",
        audio_cue="Jaga irama konstan dan mendarat perlahan dengan ujung telapak kaki."
    ),
    Exercise(
        id="ex_high_knees",
        name="High Knees Cardio",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=8.5,
        equipment_needed="None",
        instructions=[
            "Lari di tempat sambil mengangkat lutut setinggi mungkin (target setinggi pinggang).",
            "Ayunkan lengan selaras dengan hentakan kaki berlawanan.",
            "Pertahankan kecepatan dan mendarat dengan lembut."
        ],
        accessible_description="Gerakan lari di tempat dengan lutut diangkat tinggi ke arah dada.",
        audio_cue="Angkat lutut tinggi dan jaga punggung tetap tegak."
    ),
    Exercise(
        id="ex_burpees",
        name="Full Body Burpees",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.ADVANCED,
        met_value=11.0,
        equipment_needed="None",
        instructions=[
            "Dari posisi berdiri, jongkok dan letakkan telapak tangan di lantai.",
            "Tendang kedua kaki ke belakang menjadi posisi push-up plank.",
            "Lakukan satu gerakan push-up, lalu tarik kaki kembali ke depan.",
            "Lompat ke atas secara eksplosif dengan tangan terangkat ke atas."
        ],
        accessible_description="Kombinasi jongkok, tendang ke posisi plank push-up, tarik kaki, lalu lompat ke atas.",
        audio_cue="Dorong tubuh secara eksplosif saat melompat dan mendarat dengan lembut."
    ),
    Exercise(
        id="ex_mountain_climbers",
        name="Mountain Climbers",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=9.0,
        equipment_needed="None",
        instructions=[
            "Posisikan tubuh dalam posisi high plank dengan kedua telapak tangan menopang tubuh.",
            "Tarik lutut kanan ke arah dada secara cepat, lalu ganti dengan lutut kiri.",
            "Lakukan gerakan seperti berlari mendaki secara konsisten."
        ],
        accessible_description="Gerakan lari mendaki secara dinamis saat tubuh bertumpu pada kedua tangan dalam posisi push-up.",
        audio_cue="Jaga pinggul tetap stabil dan tidak naik terlalu tinggi."
    ),

    # ---- ABS & CORE ----
    Exercise(
        id="ex_crunches",
        name="Abdominal Crunches",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=5.0,
        equipment_needed="Matras",
        instructions=[
            "Berbaring telentang dengan lutut ditekuk dan telapak kaki menapak rata.",
            "Letakkan jari tangan di samping pelipis atau di belakang telinga tanpa menarik leher.",
            "Kontraksikan otot perut untuk mengangkat bahu beberapa sentimeter dari lantai.",
            "Turunkan perlahan dengan kendali penuh."
        ],
        accessible_description="Berbaring telentang dan menggulung bahu ke atas menggunakan kekuatan perut tanpa menarik kepala.",
        audio_cue="Hembuskan napas saat naik, jangan tarik lehermu."
    ),
    Exercise(
        id="ex_plank",
        name="Forearm Plank",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=4.0,
        equipment_needed="Matras",
        instructions=[
            "Letakkan lengan bawah di lantai dengan siku sejajar tepat di bawah bahu.",
            "Luruskan kaki ke belakang dengan jari-jari kaki bertumpu di lantai.",
            "Kencangkan perut dan bokong, jaga tubuh lurus dari kepala hingga tumit."
        ],
        accessible_description="Menahan tubuh lurus sejajar lantai bertumpu pada lengan bawah dan ujung jari kaki.",
        audio_cue="Tarik pusar ke arah tulang belakang dan tetap bernapas teratur."
    ),
    Exercise(
        id="ex_leg_raises",
        name="Lying Leg Raises",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=5.5,
        equipment_needed="Matras",
        instructions=[
            "Berbaring telentang dengan tangan di samping tubuh untuk stabilitas.",
            "Jaga kedua kaki tetap lurus, lalu angkat ke atas hingga membentuk sudut 90 derajat.",
            "Turunkan kaki perlahan hingga hampir menyentuh lantai tanpa membiarkan punggung bawah melengkung."
        ],
        accessible_description="Berbaring telentang lalu mengangkat kedua kaki lurus ke atas dan menurunkannya secara perlahan.",
        audio_cue="Tekan punggung bawahmu rata ke lantai sepanjang gerakan."
    ),
    Exercise(
        id="ex_russian_twists",
        name="Russian Twists",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=6.0,
        equipment_needed="Matras",
        instructions=[
            "Duduk dengan lutut ditekuk dan condongkan torso ke belakang sekitar 45 derajat.",
            "Angkat sedikit kaki dari lantai untuk keseimbangan (opsional).",
            "Putar torso ke kanan secara penuh, lalu putar ke kiri secara terkontrol."
        ],
        accessible_description="Duduk condong dan memutar tubuh bagian atas dari sisi kanan ke kiri untuk melatih otot samping perut.",
        audio_cue="Fokuskan putaran dari otot perut sampingmu, bukan hanya menggerakkan tangan."
    ),
    Exercise(
        id="ex_bicycle_crunches",
        name="Bicycle Crunches",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.ADVANCED,
        met_value=7.5,
        equipment_needed="Matras",
        instructions=[
            "Berbaring telentang, angkat kedua kaki dengan lutut ditekuk 90 derajat.",
            "Sentuhkan siku kanan ke lutut kiri sambil meluruskan kaki kanan ke depan.",
            "Ganti arah secara berirama seperti mengayuh sepeda."
        ],
        accessible_description="Mengayuh kaki seperti bersepeda di udara sambil menyentuhkan siku menyilang ke lutut yang berlawanan.",
        audio_cue="Lakukan secara terkontrol dan rasakan kontraksi di setiap putaran."
    ),

    # ---- CHEST & UPPER BODY ----
    Exercise(
        id="ex_knee_pushups",
        name="Knee Push-ups",
        target_muscle=MuscleGroup.CHEST,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=5.0,
        equipment_needed="Matras",
        instructions=[
            "Mulai dengan posisi push-up tetapi tumpukan berat tubuh bawah pada lutut.",
            "Turunkan dada ke arah lantai hingga siku membentuk sudut 90 derajat.",
            "Dorong tubuh kembali ke atas dengan telapak tangan."
        ],
        accessible_description="Gerakan push-up dengan lutut menempel di lantai untuk meringankan beban tubuh.",
        audio_cue="Jaga garis lurus dari lutut hingga kepala."
    ),
    Exercise(
        id="ex_pushups",
        name="Standard Push-ups",
        target_muscle=MuscleGroup.CHEST,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=7.0,
        equipment_needed="None",
        instructions=[
            "Posisi plank bertumpu pada telapak tangan dan ujung jari kaki, tangan selebar bahu.",
            "Turunkan dada mendekati lantai dengan siku mengarah ke belakang sekitar 45 derajat.",
            "Dorong lantai kuat-kuat untuk kembali ke posisi awal."
        ],
        accessible_description="Menurunkan dan mendorong seluruh bobot tubuh menggunakan kekuatan dada dan lengan dari posisi plank lurus.",
        audio_cue="Kencangkan perut dan jangan biarkan pinggul merosot ke bawah."
    ),
    Exercise(
        id="ex_diamond_pushups",
        name="Diamond Push-ups",
        target_muscle=MuscleGroup.CHEST,
        difficulty=DifficultyLevel.ADVANCED,
        met_value=8.5,
        equipment_needed="None",
        instructions=[
            "Posisikan tangan rapat di bawah dada hingga ibu jari dan telunjuk saling bersentuhan membentuk segitiga/berlian.",
            "Turunkan dada ke arah tangan berlian, jaga siku tetap dekat dengan tubuh.",
            "Dorong kembali ke atas menggunakan kekuatan dada bagian dalam dan trisep."
        ],
        accessible_description="Push-up intensif dengan telapak tangan dirapatkan di bawah dada membentuk segitiga.",
        audio_cue="Jaga stabilitas siku dan dorong kuat melalui telapak tangan."
    ),

    # ---- ARMS & SHOULDERS ----
    Exercise(
        id="ex_arm_circles",
        name="Arm Circles",
        target_muscle=MuscleGroup.ARMS,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=3.5,
        equipment_needed="None",
        instructions=[
            "Berdiri tegak dan rentangkan kedua tangan lurus ke samping sejajar bahu.",
            "Putar lengan membentuk lingkaran kecil ke depan secara berirama.",
            "Ubah arah putaran ke belakang setelah separuh waktu."
        ],
        accessible_description="Merentangkan kedua tangan ke samping dan memutarnya secara melingkar untuk memanaskan otot bahu.",
        audio_cue="Tahan tangan tetap sejajar bahu tanpa menurunkannya."
    ),
    Exercise(
        id="ex_tricep_dips",
        name="Chair Tricep Dips",
        target_muscle=MuscleGroup.ARMS,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=5.0,
        equipment_needed="Kursi kokoh / Undakan",
        instructions=[
            "Duduk di tepi kursi, letakkan tangan di tepi di samping pinggul.",
            "Geser pinggul ke depan keluar dari kursi dengan lengan lurus menopang tubuh.",
            "Tekuk siku ke belakang untuk menurunkan tubuh hingga lengan atas sejajar lantai.",
            "Dorong kembali ke atas menggunakan kekuatan trisep."
        ],
        accessible_description="Menurunkan dan menaikkan tubuh menggunakan kekuatan trisep bertumpu pada tepi kursi atau meja rendah.",
        audio_cue="Jaga punggung tetap dekat dengan tepi kursi dan siku menekuk lurus ke belakang."
    ),
    Exercise(
        id="ex_pike_pushups",
        name="Pike Push-ups",
        target_muscle=MuscleGroup.ARMS,
        difficulty=DifficultyLevel.ADVANCED,
        met_value=8.0,
        equipment_needed="None",
        instructions=[
            "Bentuk tubuh seperti huruf V terbalik (posisi downward dog), pinggul terangkat tinggi.",
            "Tekuk siku untuk menurunkan kepala ke arah lantai di antara kedua tangan.",
            "Dorong kembali ke posisi V menggunakan kekuatan bahu dan trisep."
        ],
        accessible_description="Push-up bahu dari posisi V terbalik dengan pinggul tinggi, menargetkan otot deltoid bahu dan lengan atas.",
        audio_cue="Fokuskan dorongan pada otot bahumu dan tatap ke arah kaki."
    ),

    # ---- LEGS & GLUTES ----
    Exercise(
        id="ex_glute_bridges",
        name="Glute Bridges",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=4.0,
        equipment_needed="Matras",
        instructions=[
            "Berbaring telentang, tekuk lutut dengan telapak kaki menapak kuat di lantai selebar pinggul.",
            "Dorong melalui tumit dan kencangkan bokong untuk mengangkat pinggul ke atas.",
            "Tahan sejenak di puncak gerakan lalu turunkan kembali secara perlahan."
        ],
        accessible_description="Berbaring telentang lalu mendorong pinggul ke atas menggunakan kekuatan otot pantat dan paha belakang.",
        audio_cue="Remas otot bokongmu di posisi atas selama 1 detik."
    ),
    Exercise(
        id="ex_wall_sit",
        name="Wall Sit",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=4.5,
        equipment_needed="Dinding",
        instructions=[
            "Sandarkan punggung rata pada dinding.",
            "Geser ke bawah hingga paha sejajar dengan lantai (sudut lutut 90 derajat).",
            "Tahan posisi diam ini sambil bernapas tenang."
        ],
        accessible_description="Posisi duduk statis menyandarkan punggung pada dinding dengan lutut menekuk 90 derajat.",
        audio_cue="Pertahankan punggung menempel erat di dinding dan jangan letakkan tangan di lutut."
    ),
    Exercise(
        id="ex_bodyweight_squats",
        name="Bodyweight Squats",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=5.5,
        equipment_needed="None",
        instructions=[
            "Berdiri dengan kaki selebar bahu, jari kaki sedikit mengarah ke luar.",
            "Dorong pinggul ke belakang dan tekuk lutut seolah hendak duduk di kursi.",
            "Turun hingga paha minimal sejajar dengan lantai, lalu dorong melalui tumit untuk berdiri."
        ],
        accessible_description="Gerakan jongkok berdiri menekuk lutut dan pinggul sambil menjaga dada tetap tegak.",
        audio_cue="Tumpukan berat pada tumit dan jaga dada tetap tegap menghadap ke depan."
    ),
    Exercise(
        id="ex_lunges",
        name="Walking Lunges",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.INTERMEDIATE,
        met_value=6.0,
        equipment_needed="None",
        instructions=[
            "Langkahkan satu kaki ke depan, turunkan pinggul hingga kedua lutut membentuk sudut 90 derajat.",
            "Lutut depan tepat di atas pergelangan kaki, lutut belakang hampir menyentuh lantai.",
            "Dorong kembali dan ganti kaki berikutnya."
        ],
        accessible_description="Melangkah lebar ke depan dan merendahkan tubuh hingga kedua lutut membentuk sudut siku-siku secara bergantian.",
        audio_cue="Jaga tubuh tegak dan langkah yang seimbang."
    ),
    Exercise(
        id="ex_jump_squats",
        name="Explosive Jump Squats",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.ADVANCED,
        met_value=9.5,
        equipment_needed="None",
        instructions=[
            "Lakukan gerakan squat hingga paha sejajar lantai.",
            "Dorong kaki dengan kekuatan penuh untuk melompat tinggi ke udara.",
            "Mendarat dengan lembut langsung ke posisi squat berikutnya secara halus."
        ],
        accessible_description="Gerakan squat dinamis yang diakhiri dengan lompatan eksplosif ke atas dan mendarat kembali menyerap ke squat.",
        audio_cue="Mendaratlah dengan lentur dan lembut pada ujung telapak kaki untuk melindungi persendian."
    ),

    # ---- BACK & SPINE POSTURE ----
    Exercise(
        id="ex_bird_dog",
        name="Bird Dog Core & Back",
        target_muscle=MuscleGroup.BACK,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=3.5,
        equipment_needed="Matras",
        instructions=[
            "Mulai dengan posisi merangkak (tangan di bawah bahu, lutut di bawah pinggul).",
            "Rentangkan tangan kanan ke depan dan kaki kiri lurus ke belakang secara bersamaan.",
            "Tahan 2 detik lalu kembali dan ulangi pada sisi berlawanan."
        ],
        accessible_description="Posisi merangkak lalu meluruskan tangan dan kaki yang berlawanan arah secara bergantian untuk kestabilan punggung.",
        audio_cue="Jaga tulang belakang tetap lurus dan seimbang tanpa miring."
    ),
    Exercise(
        id="ex_superman",
        name="Superman Back Extension",
        target_muscle=MuscleGroup.BACK,
        difficulty=DifficultyLevel.BEGINNER,
        met_value=4.0,
        equipment_needed="Matras",
        instructions=[
            "Tidur tengkurap dengan tangan terentang lurus ke depan dan kaki lurus ke belakang.",
            "Angkat lengan, dada, dan kaki secara bersamaan beberapa sentimeter dari lantai.",
            "Tahan kontraksi di otot punggung sejenak lalu turunkan perlahan."
        ],
        accessible_description="Tengkurap di lantai lalu mengangkat dada, kedua lengan, dan kaki ke atas menyerupai posisi terbang.",
        audio_cue="Rasakan kontraksi di sepanjang punggung dan jangan menolehkan kepala ke samping."
    )
]


def _build_routine_from_spec(
    routine_id: str,
    title: str,
    description: str,
    target_muscle: MuscleGroup,
    difficulty: DifficultyLevel,
    tags: List[str],
    exercise_ids: List[str],
    ex_map: Dict[str, Exercise]
) -> WorkoutRoutine:
    """
    Constructs a WorkoutRoutine according to exact difficulty rules:
    - Beginner: 20s work, 20s rest
    - Intermediate: 30s work, 15s rest
    - Advanced: 45s work, 10s rest
    """
    if difficulty == DifficultyLevel.BEGINNER:
        work_sec = 20
        rest_sec = 20
    elif difficulty == DifficultyLevel.INTERMEDIATE:
        work_sec = 30
        rest_sec = 15
    else:  # ADVANCED
        work_sec = 45
        rest_sec = 10

    steps = []
    for idx, ex_id in enumerate(exercise_ids):
        steps.append(WorkoutStep(
            step_id=f"step_{idx+1}",
            step_type=StepType.EXERCISE,
            duration_seconds=work_sec,
            exercise=ex_map[ex_id]
        ))
        # Add rest between exercises
        if idx < len(exercise_ids) - 1:
            steps.append(WorkoutStep(
                step_id=f"step_{idx+1}_rest",
                step_type=StepType.REST,
                duration_seconds=rest_sec
            ))

    return WorkoutRoutine(
        id=routine_id,
        title=title,
        description=description,
        target_muscle=target_muscle,
        difficulty=difficulty,
        tags=tags,
        cover_image=f"workout_data/images/covers/cover_{routine_id}.png",
        steps=steps
    )


def build_default_routines(exercises: List[Exercise]) -> List[WorkoutRoutine]:
    """
    Generates rich pre-packaged templates for all muscle groups and difficulty tiers.
    """
    ex_map = {ex.id: ex for ex in exercises}
    routines: List[WorkoutRoutine] = []

    # 1. FULL BODY TEMPLATES
    routines.append(_build_routine_from_spec(
        routine_id="routine_fb_beginner",
        title="Full Body Pemula: Pondasi Kebugaran",
        description="Latihan ramah sendi untuk mengaktifkan seluruh tubuh tanpa rasa lelah berlebih. Ideal untuk baru mulai berolahraga.",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.BEGINNER,
        tags=["Full Body", "Pemula", "Low Impact"],
        exercise_ids=["ex_jumping_jacks", "ex_wall_sit", "ex_knee_pushups", "ex_crunches", "ex_bird_dog"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_7min_fullbody",
        title="Scientific 7-Minute HIIT Full Body",
        description="Rangkaian 8 gerakan berintensitas sedang berbasis riset olahraga untuk membakar kalori dan membentuk otot.",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.INTERMEDIATE,
        tags=["Full Body", "HIIT", "Cardio", "Popular"],
        exercise_ids=["ex_jumping_jacks", "ex_pushups", "ex_bodyweight_squats", "ex_crunches", "ex_plank", "ex_high_knees", "ex_tricep_dips", "ex_lunges"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_fb_advanced",
        title="Spartan Beast: Full Body Calisthenics",
        description="Latihan eksplosif durasi 45 detik dengan istirahat singkat 10 detik untuk daya tahan otot dan pembakaran lemak maksimal.",
        target_muscle=MuscleGroup.FULL_BODY,
        difficulty=DifficultyLevel.ADVANCED,
        tags=["Full Body", "Advanced", "Fat Burn", "Extreme"],
        exercise_ids=["ex_burpees", "ex_mountain_climbers", "ex_jump_squats", "ex_diamond_pushups", "ex_bicycle_crunches", "ex_high_knees", "ex_pike_pushups", "ex_plank"],
        ex_map=ex_map
    ))

    # 2. ABS & CORE TEMPLATES
    routines.append(_build_routine_from_spec(
        routine_id="routine_abs_beginner",
        title="Perut Rata & Core Sehat (Pemula)",
        description="Memperkuat otot perut dan stabilitas tulang belakang dengan gerakan terkontrol dan aman bagi leher.",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.BEGINNER,
        tags=["Abs", "Core", "Pemula"],
        exercise_ids=["ex_crunches", "ex_plank", "ex_bird_dog", "ex_glute_bridges"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_core_blast",
        title="Six-Pack Sculptor & Oblique Burn",
        description="Fokus pembentukan otot rectus abdominis dan otot perut samping (obliques) dengan tempo ritmis.",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.INTERMEDIATE,
        tags=["Abs", "Core", "Sixpack"],
        exercise_ids=["ex_crunches", "ex_plank", "ex_russian_twists", "ex_leg_raises", "ex_mountain_climbers", "ex_plank"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_abs_advanced",
        title="Iron Core: Abdominals of Steel",
        description="Latihan otot perut intensif tanpa ampun berdurasi 45 detik per sesi untuk pemisahan otot yang tegas.",
        target_muscle=MuscleGroup.ABS_CORE,
        difficulty=DifficultyLevel.ADVANCED,
        tags=["Abs", "Extreme", "Core"],
        exercise_ids=["ex_bicycle_crunches", "ex_leg_raises", "ex_russian_twists", "ex_mountain_climbers", "ex_plank", "ex_crunches"],
        ex_map=ex_map
    ))

    # 3. ARMS & UPPER BODY TEMPLATES
    routines.append(_build_routine_from_spec(
        routine_id="routine_arms_beginner",
        title="Lengan Kencang & Bahu Tegak (Pemula)",
        description="Membentuk otot lengan dan bahu dengan beban tubuh ringan tanpa perlu dumbbell.",
        target_muscle=MuscleGroup.ARMS,
        difficulty=DifficultyLevel.BEGINNER,
        tags=["Arms", "Bahu", "Pemula"],
        exercise_ids=["ex_arm_circles", "ex_knee_pushups", "ex_tricep_dips", "ex_bird_dog"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_arms_intermediate",
        title="Upper Body Push & Tricep Sculpt",
        description="Kombinasi push-up standar dan tricep dips untuk memperbesar tonus otot lengan dan bahu.",
        target_muscle=MuscleGroup.ARMS,
        difficulty=DifficultyLevel.INTERMEDIATE,
        tags=["Arms", "Trisep", "Bahu"],
        exercise_ids=["ex_pushups", "ex_tricep_dips", "ex_arm_circles", "ex_pushups", "ex_plank"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_arms_advanced",
        title="Pike & Diamond Arm Destroyer",
        description="Tantangan kalistenik tingkat lanjut mengisolasi trisep dan deltoid bahu.",
        target_muscle=MuscleGroup.ARMS,
        difficulty=DifficultyLevel.ADVANCED,
        tags=["Arms", "Advanced", "Strength"],
        exercise_ids=["ex_diamond_pushups", "ex_pike_pushups", "ex_tricep_dips", "ex_pushups", "ex_diamond_pushups"],
        ex_map=ex_map
    ))

    # 4. LEGS & LOWER BODY TEMPLATES
    routines.append(_build_routine_from_spec(
        routine_id="routine_legs_glutes",
        title="Kaki Kuat & Bokong Kencang (Pemula)",
        description="Latihan paha dan gluteus dengan gerakan squat terkontrol dan wall sit penenang sendi.",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.BEGINNER,
        tags=["Legs", "Paha", "Glutes", "Pemula"],
        exercise_ids=["ex_bodyweight_squats", "ex_wall_sit", "ex_glute_bridges", "ex_lunges"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_legs_intermediate",
        title="Quad & Hamstring Power Builder",
        description="Rangkaian lunge dan squat dinamis untuk membentuk otot kaki yang kuat dan atletis.",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.INTERMEDIATE,
        tags=["Legs", "Lower Body", "Cardio"],
        exercise_ids=["ex_bodyweight_squats", "ex_lunges", "ex_wall_sit", "ex_glute_bridges", "ex_high_knees", "ex_bodyweight_squats"],
        ex_map=ex_map
    ))
    routines.append(_build_routine_from_spec(
        routine_id="routine_legs_advanced",
        title="Explosive Plyometric Leg Blast",
        description="Latihan melompat tingkat tinggi untuk meningkatkan daya ledak otot paha dan betis.",
        target_muscle=MuscleGroup.LEGS,
        difficulty=DifficultyLevel.ADVANCED,
        tags=["Legs", "Plyometrics", "Explosive"],
        exercise_ids=["ex_jump_squats", "ex_lunges", "ex_high_knees", "ex_bodyweight_squats", "ex_wall_sit", "ex_jump_squats"],
        ex_map=ex_map
    ))

    # 5. BACK & POSTURE TEMPLATES
    routines.append(_build_routine_from_spec(
        routine_id="routine_back_posture",
        title="Koreksi Postur & Punggung Sehat",
        description="Mengurangi pegal akibat duduk seharian di depan laptop dan memperkuat otot penyangga tulang belakang.",
        target_muscle=MuscleGroup.BACK,
        difficulty=DifficultyLevel.BEGINNER,
        tags=["Back", "Postur", "Spine", "Pegal"],
        exercise_ids=["ex_bird_dog", "ex_superman", "ex_bird_dog", "ex_superman", "ex_plank"],
        ex_map=ex_map
    ))

    return routines


def build_default_weekly_schedule(routines: List[WorkoutRoutine]) -> WeeklySchedule:
    """
    Builds a balanced default 7-day schedule (e.g. Mon: Full Body, Tue: Rest, etc.)
    """
    r_map = {r.id: r for r in routines}

    fb = r_map.get("routine_7min_fullbody") or routines[0]
    core = r_map.get("routine_core_blast") or routines[1]
    legs = r_map.get("routine_legs_glutes") or routines[2]
    arms = r_map.get("routine_arms_intermediate") or routines[0]

    days = {
        DayOfWeek.SENIN.value: DailySchedule(
            day=DayOfWeek.SENIN.value,
            is_rest_day=False,
            routine_id=fb.id,
            routine_title=fb.title,
            scheduled_time="06:30"
        ),
        DayOfWeek.SELASA.value: DailySchedule(
            day=DayOfWeek.SELASA.value,
            is_rest_day=False,
            routine_id=core.id,
            routine_title=core.title,
            scheduled_time="07:00"
        ),
        DayOfWeek.RABU.value: DailySchedule(
            day=DayOfWeek.RABU.value,
            is_rest_day=True,
            routine_id=None,
            routine_title=None,
            scheduled_time="07:00"
        ),
        DayOfWeek.KAMIS.value: DailySchedule(
            day=DayOfWeek.KAMIS.value,
            is_rest_day=False,
            routine_id=legs.id,
            routine_title=legs.title,
            scheduled_time="06:30"
        ),
        DayOfWeek.JUMAT.value: DailySchedule(
            day=DayOfWeek.JUMAT.value,
            is_rest_day=False,
            routine_id=arms.id,
            routine_title=arms.title,
            scheduled_time="17:00"
        ),
        DayOfWeek.SABTU.value: DailySchedule(
            day=DayOfWeek.SABTU.value,
            is_rest_day=False,
            routine_id=fb.id,
            routine_title=fb.title,
            scheduled_time="08:00"
        ),
        DayOfWeek.MINGGU.value: DailySchedule(
            day=DayOfWeek.MINGGU.value,
            is_rest_day=True,
            routine_id=None,
            routine_title=None,
            scheduled_time="08:00"
        )
    }

    return WeeklySchedule(schedule_id="user_schedule", days=days)
