/** Testbed limits, quoted from PREREGISTRATION.md s6, RESULTS_2026-10-05.md s6 and the story guide ch. 7. */
export const LIMITS: { title: string; text: string; source: string }[] = [
  {
    title: "Software timestamping",
    text: "No PTP hardware clock (/dev/ptp* is empty). Timestamp noise is at the microsecond scale while the targets are nanoseconds, so no claim is made about absolute time-error size.",
    source: "Story guide ch. 7",
  },
  {
    title: "free_running 1: clocks never steered",
    text: "Every ptp4l daemon runs with free_running 1 on one shared oscillator. Offsets are measured but no clock is steered and the host clock is never touched. Outcomes are who the RUs follow (parent, grandmaster, port state), not nanosecond time error.",
    source: "PREREGISTRATION §2, §6; RESULTS §6",
  },
  {
    title: "Network namespaces on one host",
    text: "Six real linuxptp 4.0 daemons in Linux network namespaces, wired by veth pairs into two software bridges. No hardware, no GNSS receiver, no SyncE PHY; oscillator drift, holdover, GNSS spoofing/jamming and SyncE classes cannot be produced.",
    source: "PREREGISTRATION §2; story guide ch. 7",
  },
  {
    title: "nftables bridge filter ≠ switch ACL or Annex P",
    text: "Isolation is an nftables bridge rule dropping ethertype 0x88F7 at the offending port. It stands in for a switch-port PTP filter; it is not IEEE 1588-2019 Annex P authentication (linuxptp 4.0 has none).",
    source: "RESULTS §6; STANDARDS_EVIDENCE §1",
  },
  {
    title: "No digital twin",
    text: "Actions are verified after execution on the live testbed, not rehearsed beforehand in a twin.",
    source: "PREREGISTRATION §6; RESULTS §6",
  },
  {
    title: "Small sample",
    text: "5 replicates per arm per scenario; intervals are wide (H3: 1/25, Wilson 95 % [0.007, 0.195]).",
    source: "RESULTS §2, §6",
  },
  {
    title: "Inherited detector limits",
    text: "The loop uses the campaign's frozen rule unchanged, including the ~60 % interception evasion band and the base rule's false A8 on a provisioned replacement BC (neutralised by the guard, not fixed).",
    source: "PREREGISTRATION §6; RESULTS §6",
  },
  {
    title: "Collateral on RU3",
    text: "Where the injector shares RU3's port (A2, A3, A5, C2, C3), isolation also stops RU3's own Delay_Req. In C3, RU3 kept following the forger for the whole run.",
    source: "RESULTS §6",
  },
];

export function LimitsPanel() {
  return (
    <ul className="mt-3 grid gap-3 md:grid-cols-2" data-testid="limits-panel">
      {LIMITS.map((l) => (
        <li key={l.title} className="rounded-lg border border-line bg-surface p-4">
          <p className="font-semibold">{l.title}</p>
          <p className="mt-1 text-sm">{l.text}</p>
          <p className="mt-1 text-xs text-muted">Source: {l.source}</p>
        </li>
      ))}
    </ul>
  );
}
