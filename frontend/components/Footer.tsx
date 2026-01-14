import { Separator } from "@/components/ui/separator";

export default function Footer() {
  return (
    <footer className="mt-auto bg-white">
      <Separator />

      <div className="mx-auto max-w-6xl px-4 py-6 text-xs text-black/60">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            © {new Date().getFullYear()} NMBU – Intern prototype
          </div>

          <div className="flex gap-4">
            <a
              href="#"
              className="hover:underline"
            >
              Personvern
            </a>
            <a
              href="#"
              className="hover:underline"
            >
              Tilgjengelighet
            </a>
            <a
              href="#"
              className="hover:underline"
            >
              Kontakt
            </a>
          </div>
        </div>

        <p className="mt-3 max-w-3xl text-[11px] leading-relaxed">
          Denne chatboten gir kun veiledende svar basert på tilgjengelig og
          verifiserbar informasjon. Dersom informasjon ikke finnes, vil svaret være:
          «Jeg har dessverre ikke tilgang på denne informasjonen.»
        </p>
      </div>
    </footer>
  );
}
