# registration_refactor.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Dict


# ------------------------------
# Bagian A: Kode Bermasalah (Before)
# ------------------------------
@dataclass
class StudentRegistration:
    student_id: str
    name: str
    current_sks: int
    requested_sks: int
    completed_courses: List[str]
    requested_courses: List[str]
    schedule: List[str]


class ValidatorManager:  # God-class (contoh sebelum refactor)
    def validate(self, reg: StudentRegistration) -> bool:
        print("ValidatorManager: memulai validasi gabungan...")
        if reg.current_sks + reg.requested_sks > 24:
            print("Gagal: Melebihi batas SKS (max 24).")
            return False

        for course in reg.requested_courses:
            if course == "CS201" and "CS101" not in reg.completed_courses:
                print("Gagal: Prasyarat CS101 belum terpenuhi untuk CS201.")
                return False

        # BUG di versi lama: loop dan kondisi yang selalu True.
        # Hanya contoh: tidak melakukan apa-apa di sini.
        # (ini bagian "before" - tidak dipakai di versi refactor)
        for slot in reg.schedule:
            if slot in reg.schedule:
                pass

        print("Semua pengecekan ValidatorManager terlewati.")
        return True


# ------------------------------
# Bagian B: Refactor SOLID
# ------------------------------

class IValidationRule(ABC):
    @abstractmethod
    def validate(self, reg: StudentRegistration) -> Tuple[bool, str]:
        """
        Kembalikan (True, "") jika lulus;
        jika gagal return (False, "Pesan kesalahan")
        """
        raise NotImplementedError


# Rule 1 – SKS limit
class SksLimitRule(IValidationRule):
    def __init__(self, max_sks: int = 24):
        self.max_sks = max_sks

    def validate(self, reg: StudentRegistration) -> Tuple[bool, str]:
        if reg.current_sks + reg.requested_sks > self.max_sks:
            return False, f"Gagal: Melebihi batas SKS (max {self.max_sks})."
        return True, ""


# Rule 2 – Prasyarat
class PrerequisiteRule(IValidationRule):
    def __init__(self, prereq_map: Dict[str, List[str]]):
        """
        prereq_map: dict, key = course, value = list of prerequisite course codes
        contoh: {"CS201": ["CS101"]}
        """
        self.prereq_map = prereq_map

    def validate(self, reg: StudentRegistration) -> Tuple[bool, str]:
        for course in reg.requested_courses:
            required = self.prereq_map.get(course, [])
            for req in required:
                if req not in reg.completed_courses:
                    return False, f"Gagal: Prasyarat {req} belum terpenuhi untuk {course}."
        return True, ""


# Rule 3 – Jadwal Bentrok (OCP Extension)
class JadwalBentrokRule(IValidationRule):
    def __init__(self, existing_schedule: List[str] = None, course_slot_map: Dict[str, str] = None):
        # existing_schedule: jadwal yang sudah terdaftar (mis. jam kuliah saat ini)
        self.existing_schedule = existing_schedule or []
        # memungkinkan injeksi mapping course->slot dari luar untuk fleksibilitas
        self.course_slot_map = course_slot_map or {
            "CS101": "Mon-09",
            "CS102": "Tue-11",
            "CS201": "Mon-09",
            "MA101": "Wed-10",
        }

    def validate(self, reg: StudentRegistration) -> Tuple[bool, str]:
        # Buat set occupied dari jadwal existing + jadwal yang sudah dimiliki di reg.schedule
        occupied = set(self.existing_schedule + reg.schedule)

        # cek setiap requested course apakah slotnya sudah terpakai
        for course in reg.requested_courses:
            slot = self.course_slot_map.get(course)
            if slot is None:
                # tanpa mapping, anggap aman
                continue
            if slot in occupied:
                return False, f"Gagal: Jadwal bentrok untuk {course} pada slot {slot}."
            # tambahkan ke occupied agar mencegah bentrok antar requested courses
            occupied.add(slot)

        return True, ""


# Coordinator: RegistrationService (SRP) — menerima list of IValidationRule via DI
class RegistrationService:
    def __init__(self, rules: List[IValidationRule]):
        self.rules = rules

    def register(self, reg: StudentRegistration) -> Tuple[bool, str]:
        for rule in self.rules:
            ok, msg = rule.validate(reg)
            rule_name = rule.__class__.__name__
            print(f"[{rule_name}] -> {'OK' if ok else 'FAIL'}{(' - ' + msg) if msg else ''}")
            if not ok:
                return False, msg
        return True, "Registrasi berhasil."


# ------------------------------
# Bagian C: Demonstrasi & Pembuktian OCP
# ------------------------------
def demo_before_refactor():
    print("\n=== Demo BEFORE refactor (ValidatorManager) ===")
    reg = StudentRegistration(
        student_id="S001",
        name="Ani",
        current_sks=20,
        requested_sks=6,
        completed_courses=["CS101"],
        requested_courses=["CS201"],
        schedule=["Tue-11"]
    )
    vm = ValidatorManager()
    ok = vm.validate(reg)
    print("Hasil ValidatorManager:", ok)
    print()


def demo_after_refactor(include_jadwal_rule: bool = False):
    print("\n=== Demo AFTER refactor (RegistrationService with Rules) ===")
    reg = StudentRegistration(
        student_id="S002",
        name="Budi",
        current_sks=18,
        requested_sks=6,  # total 24 => batas
        completed_courses=["CS101"],
        requested_courses=["CS201", "MA101"],
        schedule=["Wed-10"]  # punya jadwal pada Wed-10
    )

    # rules: SKS limit + Prasyarat
    prereq_map = {"CS201": ["CS101"]}
    rules: List[IValidationRule] = [
        SksLimitRule(max_sks=24),
        PrerequisiteRule(prereq_map=prereq_map)
    ]

    # optional: injeksikan JadwalBentrokRule tanpa ubah RegistrationService
    if include_jadwal_rule:
        # Suppose existing schedule contains "Mon-09" so CS201 maps to Mon-09 and will conflict
        jadwal_rule = JadwalBentrokRule(existing_schedule=["Mon-09"])
        rules.append(jadwal_rule)

    service = RegistrationService(rules=rules)

    ok, msg = service.register(reg)
    print("Hasil RegistrationService:", ok, msg)
    print()


if __name__ == "__main__":
    # Demo sebelum refactor (menunjukkan kode problematik)
    demo_before_refactor()

    # Demo setelah refactor tanpa JadwalBentrokRule
    demo_after_refactor(include_jadwal_rule=False)

    # Demo setelah refactor DENGAN JadwalBentrokRule (challenge) -> menunjukkan OCP
    # Kita menambahkan rule baru ke list rules, TIDAK mengubah kode RegistrationService
    demo_after_refactor(include_jadwal_rule=True)
