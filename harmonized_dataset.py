from __future__ import annotations

import csv
from dataclasses import dataclass

from clock_features import ClockProfile


@dataclass(frozen=True)
class HarmonizedParticipant:
    seqn: str
    chronological_age: float
    profile: ClockProfile
    central_adiposity_proxy: str
    atherogenic_proxy: str
    lung_proxy: str

    def to_row(self) -> dict[str, str]:
        profile_dict = self.profile.to_dict()
        row = {
            "SEQN": self.seqn,
            "chronological_age": f"{self.chronological_age:.6f}",
            "central_adiposity_proxy": self.central_adiposity_proxy,
            "atherogenic_proxy": self.atherogenic_proxy,
            "lung_proxy": self.lung_proxy,
        }
        for key, value in profile_dict.items():
            row[key] = f"{value:.6f}"
        return row


def read_csv_rows(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_harmonized_csv(participants: list[HarmonizedParticipant], output_path: str) -> None:
    if not participants:
        raise ValueError("No harmonized participants available to write.")

    fieldnames = list(participants[0].to_row().keys())
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for participant in participants:
            writer.writerow(participant.to_row())


def load_harmonized_csv(path: str) -> list[HarmonizedParticipant]:
    rows = read_csv_rows(path)
    participants: list[HarmonizedParticipant] = []
    for row in rows:
        participants.append(
            HarmonizedParticipant(
                seqn=row["SEQN"],
                chronological_age=float(row["chronological_age"]),
                profile=ClockProfile(
                    fitness=float(row["fitness"]),
                    central_adiposity=float(row["central_adiposity"]),
                    glycemia=float(row["glycemia"]),
                    atherogenic_burden=float(row["atherogenic_burden"]),
                    hemodynamic_stress=float(row["hemodynamic_stress"]),
                    kidney_function=float(row["kidney_function"]),
                    inflammation=float(row["inflammation"]),
                    lung_function=float(row["lung_function"]),
                ),
                central_adiposity_proxy=row.get("central_adiposity_proxy", "unknown"),
                atherogenic_proxy=row.get("atherogenic_proxy", "unknown"),
                lung_proxy=row.get("lung_proxy", "unknown"),
            )
        )
    return participants
