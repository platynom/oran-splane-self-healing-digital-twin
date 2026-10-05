import type { Metadata } from "next";
import { ExplorerLoader } from "@/components/explorer/ExplorerLoader";

export const metadata: Metadata = { title: "3D O-RAN explorer" };

export default function Home() {
  return (
    <>
      <h1 className="mb-3 text-2xl font-semibold tracking-tight sm:text-3xl">O-RAN S-plane explorer</h1>
      <p className="mb-4 max-w-3xl text-muted">
        Free exploration of the whole O-RAN architecture, from the radio mast down to the open fronthaul. Bright parts belong to this project;
        dimmed parts do not. Every statement carries a citation tag and an UNVERIFIED status until it has been checked.
      </p>
      <ExplorerLoader />
    </>
  );
}
