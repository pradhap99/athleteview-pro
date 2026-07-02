"""Request bodies (camelCase JSON, per conventions). Responses are built as dicts."""

from __future__ import annotations

from pydantic import BaseModel


class CreateProjectReq(BaseModel):
    title: str
    type: str = "scripted"  # scripted | commercial | episodic
    ppStartDate: str | None = None  # ISO date; keys effective-dated rate-card resolution


class ImportScriptReq(BaseModel):
    text: str
    format: str | None = None  # fdx | fountain | pdf (inferred if omitted)


class RescheduleChangeReq(BaseModel):
    type: str = "reschedule_scene"
    sceneId: str
    toDay: int


class OptimizeReq(BaseModel):
    numDays: int
    capacityEighths: int | None = None
    timeBudgetS: float = 10.0


class FringeReq(BaseModel):
    name: str
    ratePct: float
    cap: float | None = None


class BudgetLineReq(BaseModel):
    code: str
    category: str = "other"  # atl | btl | post | other
    description: str = ""
    qty: float = 1.0
    unit: str = "flat"
    rate: float = 0.0
    fringes: list[FringeReq] = []
    driver: dict | None = None  # e.g. {"kind": "hold_day"}
    aicpSection: str | None = None


class LedgerEntryReq(BaseModel):
    """An actual or commitment against an account code (human-entered/approved)."""

    code: str
    amount: float
    memo: str = ""


class EtcReq(BaseModel):
    code: str
    amount: float


class ScriptDiffReq(BaseModel):
    text: str
    format: str | None = None


class PoCreateReq(BaseModel):
    code: str  # account code the commitment/actual books against
    vendor: str
    amount: float
    memo: str = ""


class PoReceiveReq(BaseModel):
    amount: float  # goods-receipt amount (3-way match leg)


class PoInvoiceReq(BaseModel):
    amount: float
    invoiceRef: str = ""


class CheckRequestCreateReq(BaseModel):
    code: str
    amount: float
    payee: str
    chain: list[str] = ["dept_head", "upm"]  # ordered sign-off roles


class CheckRequestApproveReq(BaseModel):
    role: str  # must match the next step in the chain


class PettyCashIssueReq(BaseModel):
    custodian: str
    floatAmount: float


class PettyCashReceiptReq(BaseModel):
    code: str
    amount: float
    memo: str = ""


class PettyCashReconcileReq(BaseModel):
    returnedCash: float


class RevisionReleaseReq(BaseModel):
    note: str = ""


class DealMemoReq(BaseModel):
    person: str
    legalName: str = ""
    department: str = ""
    # Core terms may come from a template (templateId) — explicit values always win.
    union: str | None = None  # e.g. SAG-AFTRA | IATSE | Teamsters | DGA
    contract: str | None = None  # e.g. theatrical | basic_agreement
    tier: str | None = None  # e.g. day_performer | crew | driver
    hourlyRate: float | None = None
    guaranteedHours: float | None = None  # daily guarantee — budgeted basis for hot costs
    accountCode: str | None = None
    startDate: str = ""  # ISO date
    isMinor: bool = False
    boxKitRate: float | None = None
    boxKitCadence: str = "daily"  # daily | weekly
    boxKitAccountablePlan: bool = False  # accountable plan → non-taxable reimbursement
    boxKitAccountCode: str | None = None
    templateId: str | None = None  # org deal-memo template to merge defaults from
    contactId: str | None = None  # link to the org crew DB (fills names, feeds history)


class StartPacketReq(BaseModel):
    forms: dict[str, bool]  # e.g. {"w4": true, "i9": true, "directDeposit": false}


class MealBreakReq(BaseModel):
    start: str  # ISO datetime
    end: str


class TimecardAdjustmentReq(BaseModel):
    type: str  # wardrobe | stunt | other
    amount: float
    code: str | None = None


class TimecardSubmitReq(BaseModel):
    person: str
    date: str  # ISO date
    call: str  # ISO datetime
    wrap: str
    meals: list[MealBreakReq] = []
    locationContext: str = "studio"
    dayInWeek: int = 1
    priorWrap: str | None = None
    workStatusCode: str = "W"  # Exhibit G status code
    splits: list[dict] = []  # [{code, weight}] — defaults to the memo's account code
    adjustments: list[TimecardAdjustmentReq] = []
    chain: list[str] = ["dept_head", "upm"]  # ordered approval roles


class TimecardApproveReq(BaseModel):
    role: str


class ExhibitGSignReq(BaseModel):
    date: str  # ISO date being signed


class PayrollExportReq(BaseModel):
    provider: str = "wrapbook"  # ep | castandcrew | wrapbook
    startDate: str
    endDate: str


class SidesLinkReq(BaseModel):
    dayIndex: int
    recipientName: str
    recipientEmail: str
    character: str | None = None  # character-filtered sides in one click
    expiresAt: str | None = None  # ISO datetime; None = no expiry (still revocable)
    allowDownload: bool = False
    allowPrint: bool = False


class LocationReq(BaseModel):
    name: str
    address: str = ""
    lat: float | None = None
    lng: float | None = None
    parking: str = ""
    basecamp: str = ""
    nearestHospital: str = ""


class LocationDocReq(BaseModel):
    type: str  # release | permit | coi
    issueDate: str = ""
    expiryDate: str = ""
    liabilityLimit: float | None = None  # COI
    additionalInsured: str | None = None  # COI endorsement
    reference: str = ""  # external doc pointer (vault object key)


class ContactReq(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    roles: list[str] = []  # e.g. ["Key Grip", "Best Boy"]
    union: str | None = None
    agency: str | None = None
    defaultHourlyRate: float | None = None
    notes: str = ""
    id: str | None = None  # set to update an existing contact (upsert)


class DealMemoTemplateReq(BaseModel):
    name: str  # e.g. "IATSE crew day-player"
    defaults: dict  # union/contract/tier/hourlyRate/guaranteedHours/accountCode/boxKit…


class SignatureRequestReq(BaseModel):
    docType: str  # deal_memo | release | approval
    docRef: str  # e.g. the memo person or document id
    signers: list[str]  # ORDERED signing chain


class SignReq(BaseModel):
    signer: str  # must match the next signer in order


class CallSheetPublishReq(BaseModel):
    dayIndex: int
    date: str  # ISO shoot date
    generalCall: str = "07:00"
    extraRecipients: list[dict] = []  # [{name, email, role?}] beyond the day's cast


class CallSheetAckReq(BaseModel):
    ackToken: str
