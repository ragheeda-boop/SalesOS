"use client";

import { useState, useCallback } from "react";
import { Plus, X } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { cn, Button, Input, ModalContent, ModalTrigger } from "@salesos/ui";
import type { Opportunity } from "@/lib/api";
import {
  useOpportunities,
  useCreateOpportunity,
  useAdvanceOpportunity,
  useCloseWon,
  useCloseLost,
} from "@/lib/hooks/opportunityQueries";
import { useCompanySearch } from "@/lib/hooks/companyQueries";
import { PipelineColumn } from "./PipelineColumn";

const STAGES = [
  { key: "prospecting", label: "استكشاف", color: "bg-info-500" },
  { key: "qualification", label: "تأهيل", color: "bg-indigo-500" },
  { key: "proposal", label: "عرض", color: "bg-warning-500" },
  { key: "negotiation", label: "تفاوض", color: "bg-orange-500" },
];



function CreateOpportunityModal() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [value, setValue] = useState("");
  const [companySearch, setCompanySearch] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<{
    id: string;
    name: string;
  } | null>(null);

  const { data: searchResults } = useCompanySearch({ q: companySearch, page: 1, page_size: 10 });
  const createOpportunity = useCreateOpportunity();

  const handleSubmit = async () => {
    if (!selectedCompany || !name.trim()) return;
    await createOpportunity.mutateAsync({
      companyId: selectedCompany.id,
      name: name.trim(),
      value: parseFloat(value) || 0,
    });
    setOpen(false);
    setName("");
    setValue("");
    setCompanySearch("");
    setSelectedCompany(null);
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <ModalTrigger asChild>
        <Button size="sm">
          <Plus className="ml-1 h-4 w-4" />
          فرصة جديدة
        </Button>
      </ModalTrigger>
      <ModalContent title="إنشاء فرصة جديدة">
        <div className="flex flex-col gap-4 pt-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-600">
              الشركة
            </label>
            {selectedCompany ? (
              <div className="flex items-center justify-between rounded-md border border-neutral-200 bg-white px-3 py-2 text-sm">
                <span>{selectedCompany.name}</span>
                <button
                  onClick={() => {
                    setSelectedCompany(null);
                    setCompanySearch("");
                  }}
                  className="text-neutral-400 hover:text-danger-500"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <>
                <Input
                  placeholder="ابحث عن شركة..."
                  value={companySearch}
                  onChange={(e) => setCompanySearch(e.target.value)}
                  className="mb-1"
                />
                {searchResults?.items && searchResults.items.length > 0 && (
                  <div className="max-h-40 overflow-y-auto rounded-md border border-neutral-200 bg-white">
                    {searchResults.items.slice(0, 6).map((c) => (
                      <button
                        key={c.id}
                        onClick={() =>
                          setSelectedCompany({ id: c.id, name: c.name_ar })
                        }
                        className="w-full px-3 py-1.5 text-right text-sm hover:bg-neutral-100"
                      >
                        {c.name_ar}
                        {c.cr_number && (
                          <span className="mr-2 text-xs text-neutral-400">
                            {c.cr_number}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-600">
              اسم الفرصة
            </label>
            <Input
              placeholder="مثلاً: تجديد عقد الخدمات"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-600">
              القيمة (SAR)
            </label>
            <Input
              type="number"
              placeholder="0"
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </div>
          <Button
            onClick={handleSubmit}
            disabled={!selectedCompany || !name.trim() || createOpportunity.isPending}
            className="mt-2"
          >
            {createOpportunity.isPending ? "جاري الإنشاء..." : "إنشاء"}
          </Button>
        </div>
      </ModalContent>
    </Dialog.Root>
  );
}

export function PipelineKanban() {
  const { data, isLoading, error } = useOpportunities();
  const advanceOpp = useAdvanceOpportunity();
  const closeWon = useCloseWon();
  const closeLost = useCloseLost();
  const [selectedOpp, setSelectedOpp] = useState<Opportunity | null>(null);
  const [wonAmount, setWonAmount] = useState("");
  const [lossReason, setLossReason] = useState("");
  const [closeMode, setCloseMode] = useState<"won" | "lost" | null>(null);

  const handleDrop = useCallback(
    (oppId: string, toStage: string) => {
      if (toStage === "closed_won") {
        const opp = data?.items.find((o) => o.id === oppId);
        if (opp) {
          setSelectedOpp(opp);
          setWonAmount(String(opp.value || ""));
          setCloseMode("won");
        }
        return;
      }
      if (toStage === "closed_lost") {
        const opp = data?.items.find((o) => o.id === oppId);
        if (opp) {
          setSelectedOpp(opp);
          setLossReason("");
          setCloseMode("lost");
        }
        return;
      }
      advanceOpp.mutate({ opportunityId: oppId, toStage });
    },
    [data, advanceOpp]
  );

  const handleCloseWon = async () => {
    if (!selectedOpp) return;
    await closeWon.mutateAsync({
      opportunityId: selectedOpp.id,
      amount: parseFloat(wonAmount) || undefined,
    });
    setSelectedOpp(null);
    setWonAmount("");
    setCloseMode(null);
  };

  const handleCloseLost = async () => {
    if (!selectedOpp) return;
    await closeLost.mutateAsync({
      opportunityId: selectedOpp.id,
      reason: lossReason,
    });
    setSelectedOpp(null);
    setLossReason("");
    setCloseMode(null);
  };

  if (error) {
    return (
      <div className="flex items-center justify-center py-20 text-danger-500">
        فشل تحميل الفرص. {error.message}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-neutral-400">
        جاري التحميل...
      </div>
    );
  }

  const grouped: Record<string, Opportunity[]> = {};
  const openOpportunities: Opportunity[] = [];
  const wonOpportunities: Opportunity[] = [];
  const lostOpportunities: Opportunity[] = [];

  for (const opp of data?.items ?? []) {
    if (opp.status === "won") {
      wonOpportunities.push(opp);
    } else if (opp.status === "lost") {
      lostOpportunities.push(opp);
    } else {
      openOpportunities.push(opp);
      const stage = opp.stage || "prospecting";
      if (!grouped[stage]) grouped[stage] = [];
      grouped[stage].push(opp);
    }
  }

  const totalPipeline = openOpportunities.reduce((s, o) => s + o.value, 0);

  return (
    <div className="flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">خط أنابيب المبيعات</h1>
          <p className="text-sm text-neutral-500">
            {openOpportunities.length} فرصة مفتوحة بقيمة{" "}
            <span className="font-semibold text-neutral-700">
              {formatCurrency(totalPipeline)} SAR
            </span>
          </p>
        </div>
        <CreateOpportunityModal />
      </div>

      {/* Kanban columns */}
      <div className="flex flex-col sm:flex-row gap-3 sm:overflow-x-auto pb-4">
        {STAGES.map((stage) => (
          <PipelineColumn
            key={stage.key}
            stage={stage}
            opportunities={grouped[stage.key] || []}
            onDrop={handleDrop}
          />
        ))}

        {/* Won column */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const oppId = e.dataTransfer.getData("text/plain");
            const opp = data?.items.find((o) => o.id === oppId);
            if (opp) {
              setSelectedOpp(opp);
              setWonAmount(String(opp.value || ""));
              setCloseMode("won");
            }
          }}
          className="flex w-full sm:w-[260px] shrink-0 flex-col rounded-xl border border-emerald-200 bg-emerald-50/50"
        >
          <div className="flex items-center gap-2 border-b border-emerald-200 px-3 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span className="text-sm font-semibold text-emerald-800">
              مغلقة (فوز)
            </span>
            <Badge variant="outline" className="mr-auto text-xs">
              {wonOpportunities.length}
            </Badge>
          </div>
          <div className="flex flex-col gap-2 p-2 overflow-y-auto max-h-[calc(100vh-280px)]">
            {wonOpportunities.map((opp) => (
              <OpportunityCard key={opp.id} opportunity={opp} />
            ))}
            {wonOpportunities.length === 0 && (
              <p className="py-8 text-center text-xs text-neutral-400">
                اسحب الفرصة هنا للإغلاق بالفوز
              </p>
            )}
          </div>
        </div>

        {/* Lost column */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const oppId = e.dataTransfer.getData("text/plain");
            const opp = data?.items.find((o) => o.id === oppId);
            if (opp) {
              setSelectedOpp(opp);
              setLossReason("");
              setCloseMode("lost");
            }
          }}
          className="flex w-full sm:w-[260px] shrink-0 flex-col rounded-xl border border-danger-200 bg-danger-50/50"
        >
          <div className="flex items-center gap-2 border-b border-danger-200 px-3 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-danger-500" />
            <span className="text-sm font-semibold text-danger-800">
              مغلقة (خسارة)
            </span>
            <Badge variant="outline" className="mr-auto text-xs">
              {lostOpportunities.length}
            </Badge>
          </div>
          <div className="flex flex-col gap-2 p-2 overflow-y-auto max-h-[calc(100vh-280px)]">
            {lostOpportunities.map((opp) => (
              <OpportunityCard key={opp.id} opportunity={opp} />
            ))}
            {lostOpportunities.length === 0 && (
              <p className="py-8 text-center text-xs text-neutral-400">
                اسحب الفرصة هنا للإغلاق بالخسارة
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Won confirmation dialog */}
      <Dialog.Root
        open={closeMode === "won"}
        onOpenChange={(o) => {
          if (!o) { setSelectedOpp(null); setCloseMode(null); }
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-0 shadow-muhide-6">
            <div className="border-b border-neutral-200 px-4 py-3">
              <Dialog.Title className="text-base font-semibold text-neutral-900">
                إغلاق بالفوز
              </Dialog.Title>
            </div>
            <div className="flex flex-col gap-3 p-4">
              <p className="text-sm text-neutral-600">{selectedOpp?.name}</p>
              <div>
                <label className="mb-1 block text-xs font-medium text-neutral-600">
                  قيمة الصفقة (SAR)
                </label>
                <Input
                  type="number"
                  value={wonAmount}
                  onChange={(e) => setWonAmount(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleCloseWon}
                  disabled={closeWon.isPending}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  {closeWon.isPending ? "..." : "تأكيد الفوز"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => { setSelectedOpp(null); setCloseMode(null); }}
                >
                  إلغاء
                </Button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Lost confirmation dialog */}
      <Dialog.Root
        open={closeMode === "lost"}
        onOpenChange={(o) => {
          if (!o) { setSelectedOpp(null); setCloseMode(null); }
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-black/40" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-0 shadow-muhide-6">
            <div className="border-b border-neutral-200 px-4 py-3">
              <Dialog.Title className="text-base font-semibold text-neutral-900">
                إغلاق بخسارة
              </Dialog.Title>
            </div>
            <div className="flex flex-col gap-3 p-4">
              <p className="text-sm text-neutral-600">{selectedOpp?.name}</p>
              <div>
                <label className="mb-1 block text-xs font-medium text-neutral-600">
                  سبب الخسارة
                </label>
                <Input
                  placeholder="مثلاً: السعر مرتفع"
                  value={lossReason}
                  onChange={(e) => setLossReason(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleCloseLost}
                  disabled={closeLost.isPending}
                  className="flex-1 bg-danger-600 hover:bg-danger-700"
                >
                  {closeLost.isPending ? "..." : "تأكيد الخسارة"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => { setSelectedOpp(null); setCloseMode(null); }}
                >
                  إلغاء
                </Button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
