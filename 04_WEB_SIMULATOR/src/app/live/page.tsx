import type { Metadata } from "next";
import { Card, PageTitle } from "@/components/ui";
import { LiveConsole } from "@/components/LiveConsole";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Live mode" };

export default function LivePage() {
  const onVercel = !!process.env.VERCEL;
  const url = process.env.LIVE_SERVICE_URL ?? "";
  return (
    <>
      <PageTitle
        title="Live mode (localhost only)"
        lead="Runs one real recovery-loop run with the project's harness (linuxptp in network namespaces) on your own Linux machine and streams its logs here as they are written."
      />
      {onVercel ? (
        <Card className="border-warn" data-testid="live-disabled">
          <h2 className="font-semibold">Disabled on this deployment</h2>
          <p className="mt-2 text-sm">
            Live mode needs root on a Linux host to create network namespaces, start ptp4l daemons and install nftables rules. A hosted
            serverless deployment cannot and must not do that. Use Replay for the 140 recorded runs, or run the app locally with the live
            service (see README, &quot;Live mode&quot;).
          </p>
        </Card>
      ) : !url ? (
        <Card data-testid="live-disabled">
          <h2 className="font-semibold">Live service not configured</h2>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
            <li>Install the frozen harness under /opt/sptb exactly as 03_RECOVERY_LOOP_S-PLANE/README.md describes, and check <code>sudo python3 freeze.py --verify</code> prints nothing.</li>
            <li>
              <code>cd 04_WEB_SIMULATOR/live && pip install -r requirements.txt && sudo SPTB=/opt/sptb uvicorn server:app --host 127.0.0.1 --port 8765</code>
            </li>
            <li>Set <code>LIVE_SERVICE_URL=http://127.0.0.1:8765</code> in <code>.env</code> and restart the app.</li>
          </ol>
          <p className="mt-3 text-sm text-muted">
            The service refuses to run unless the host is Linux, it runs as root, the harness tools are installed and freeze.py --verify
            passes. It never touches the host clock and only uses replicate numbers 200–999, so it cannot overwrite the evaluation runs.
          </p>
        </Card>
      ) : (
        <LiveConsole serviceUrl={url} />
      )}
    </>
  );
}
