import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./button";
import { Input } from "./input";
import { Select } from "./select";
import { Checkbox } from "./checkbox";
import { RadioGroup } from "./radio-group";
import { Switch } from "./switch";
import { Textarea } from "./textarea";
import { DatePicker } from "./date-picker";
import { Pagination } from "./pagination";
import { Skeleton } from "./skeleton";
import { EmptyState } from "./empty-state";
import { Toast, ToastProvider, ToastViewport } from "./toast";
import { Sidebar } from "./sidebar";
import { Breadcrumbs } from "./breadcrumbs";
import { DataTable } from "./data-table";
import { Combobox } from "./combobox";
import { Badge } from "./badge";
import { Avatar } from "./avatar";
import { Tooltip } from "./tooltip";
import { Spinner } from "./spinner";
import { Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter } from "./modal";
import { Tabs, TabsList, Tab, TabsPanel } from "./tabs";
import { Card, CardHeader, CardContent, CardFooter } from "./card";
import { Kbd } from "./kbd";
import { Form, FormSection, FormRow, FormField, FormActions } from "./form";
import { useState } from "react";

// ============================================================
// Form Components
// ============================================================

export default { title: "Form" } satisfies Meta;

export const ButtonStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="danger">Danger</Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm">Small</Button>
        <Button size="md">Medium</Button>
        <Button size="lg">Large</Button>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button loading>Loading</Button>
        <Button disabled>Disabled</Button>
      </div>
    </div>
  ),
};

export const InputStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Input label="Default" placeholder="Enter text..." />
      <Input label="With Error" error="This field is required" placeholder="Enter text..." />
      <Input label="Disabled" disabled placeholder="Disabled" />
    </div>
  ),
};

export const SelectStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Select
        options={[
          { label: "Option 1", value: "1" },
          { label: "Option 2", value: "2" },
          { label: "Option 3", value: "3" },
        ]}
        placeholder="Select..."
      />
      <Select
        options={[
          { label: "Option 1", value: "1" },
          { label: "Option 2", value: "2" },
        ]}
        placeholder="With error"
        error="Required"
      />
    </div>
  ),
};

export const CheckboxStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Checkbox label="Default checkbox" />
      <Checkbox label="Checked" defaultChecked />
      <Checkbox label="Indeterminate" indeterminate />
      <Checkbox label="With error" error errorMessage="Must accept terms" />
      <Checkbox label="Disabled" disabled />
      <Checkbox label="Required" required />
    </div>
  ),
};

export const RadioGroupStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <RadioGroup
        label="Select option"
        options={[
          { label: "Option A", value: "a" },
          { label: "Option B", value: "b" },
          { label: "Option C", value: "c" },
        ]}
      />
      <RadioGroup
        label="With error"
        error="Please select an option"
        options={[
          { label: "Option X", value: "x" },
          { label: "Option Y", value: "y" },
        ]}
      />
      <RadioGroup
        label="Horizontal"
        orientation="horizontal"
        options={[
          { label: "Yes", value: "yes" },
          { label: "No", value: "no" },
        ]}
      />
    </div>
  ),
};

export const SwitchStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Switch label="Wi-Fi" defaultChecked />
      <Switch label="Bluetooth" />
      <Switch label="Disabled" disabled />
      <div className="flex items-center gap-4">
        <Switch label="Small" size="sm" />
        <Switch label="Medium" size="md" />
        <Switch label="Large" size="lg" />
      </div>
    </div>
  ),
};

export const TextareaStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Textarea label="Description" placeholder="Enter description..." />
      <Textarea label="With error" error errorMessage="Cannot be empty" />
      <Textarea label="With char count" maxLength={200} value="Hello" />
      <Textarea label="Disabled" disabled />
    </div>
  ),
};

export const DatePickerStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <DatePicker label="Select date" />
      <DatePicker label="Date range" mode="range" />
      <DatePicker label="With error" error="Date required" />
    </div>
  ),
};

export const ComboboxStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Combobox
        label="Search country"
        options={[
          { label: "Saudi Arabia", value: "sa" },
          { label: "United Arab Emirates", value: "ae" },
          { label: "Kuwait", value: "kw" },
          { label: "Qatar", value: "qa" },
          { label: "Oman", value: "om" },
          { label: "Bahrain", value: "bh" },
        ]}
      />
      <Combobox
        label="With error"
        error="Required"
        options={[
          { label: "Option 1", value: "1" },
          { label: "Option 2", value: "2" },
        ]}
      />
    </div>
  ),
};

export const PaginationStory: StoryObj = {
  render: () => {
    const [page, setPage] = useState(1);
    return (
      <Pagination
        currentPage={page}
        totalPages={25}
        totalItems={487}
        pageSize={20}
        onPageChange={setPage}
        onPageSizeChange={() => {}}
      />
    );
  },
};

// ============================================================
// Navigation
// ============================================================

const NavMeta = { title: "Navigation" } satisfies Meta;
export { NavMeta };

export const SidebarStory: StoryObj = {
  render: () => (
    <div className="h-[500px] w-[256px] border rounded-lg overflow-hidden">
      <Sidebar
        collapsed={false}
        onToggle={() => {}}
        sections={[
          {
            title: "Main",
            items: [
              { label: "Dashboard", href: "/", active: true },
              { label: "Companies", href: "/companies" },
              { label: "Contacts", href: "/contacts" },
              { label: "Deals", href: "/deals" },
            ],
          },
          {
            title: "Analytics",
            items: [
              { label: "Reports", href: "/reports" },
              { label: "Forecasts", href: "/forecasts" },
              { label: "Goals", href: "/goals", badge: { count: 3, variant: "warning" as const } },
            ],
          },
        ]}
      />
    </div>
  ),
};

export const BreadcrumbsStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Companies", href: "/companies" },
          { label: "Acme Corp" },
        ]}
      />
      <Breadcrumbs
        items={[
          { label: "Home", href: "/" },
          { label: "Settings", href: "/settings" },
          { label: "Billing", href: "/settings/billing" },
          { label: "Invoices" },
        ]}
        maxItems={3}
      />
    </div>
  ),
};

// ============================================================
// Data Display
// ============================================================

const DataMeta = { title: "Data Display" } satisfies Meta;
export { DataMeta };

export const BadgeStory: StoryObj = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge>Default</Badge>
      <Badge variant="success">Active</Badge>
      <Badge variant="warning">Pending</Badge>
      <Badge variant="danger">Expired</Badge>
      <Badge variant="primary">Info</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
  ),
};

export const AvatarStory: StoryObj = {
  render: () => (
    <div className="flex items-center gap-4">
      <Avatar alt="John Doe" fallback="JD" size="sm" />
      <Avatar alt="Jane Smith" fallback="JS" size="md" />
      <Avatar alt="SalesOS" fallback="SO" size="lg" />
      <Avatar alt="Admin" fallback="AD" size="md" />
      <Avatar alt="" size="md" />
    </div>
  ),
};

export const DataTableStory: StoryObj = {
  render: () => (
    <DataTable
      columns={[
        { header: "Name", accessorKey: "name" },
        { header: "Email", accessorKey: "email" },
        { header: "Status", accessorKey: "status" },
        { header: "Role", accessorKey: "role" },
      ]}
      data={[
        { name: "John Doe", email: "john@acme.com", status: "Active", role: "Admin" },
        { name: "Jane Smith", email: "jane@acme.com", status: "Active", role: "Editor" },
        { name: "Bob Wilson", email: "bob@acme.com", status: "Inactive", role: "Viewer" },
      ]}
      sortable
    />
  ),
};

export const DataTableWithSelectionStory: StoryObj = {
  render: () => (
    <DataTable
      columns={[
        { header: "Name", accessorKey: "name" },
        { header: "Email", accessorKey: "email" },
      ]}
      data={[
        { name: "John Doe", email: "john@acme.com" },
        { name: "Jane Smith", email: "jane@acme.com" },
      ]}
      selectable
    />
  ),
};

export const SkeletonStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4 max-w-sm">
      <Skeleton variant="text" />
      <Skeleton variant="text" width="75%" />
      <Skeleton variant="card" />
      <Skeleton variant="circle" width={48} height={48} />
      <Skeleton variant="table-row" />
      <Skeleton variant="rect" width={300} height={200} />
    </div>
  ),
};

export const EmptyStateStory: StoryObj = {
  render: () => (
    <EmptyState
      title="No companies found"
      description="Try adjusting your search or filters to find what you're looking for."
      action={{ label: "Add company", onClick: () => {} }}
      learnMoreLink="/docs/companies"
    />
  ),
};

export const CardStory: StoryObj = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 max-w-2xl">
      <Card>
        <CardHeader>Card Header</CardHeader>
        <CardContent>Card content goes here. This is the main body of the card.</CardContent>
        <CardFooter>Card Footer</CardFooter>
      </Card>
      <Card>
        <CardContent>Simple card with just content.</CardContent>
      </Card>
    </div>
  ),
};

export const TabsStory: StoryObj = {
  render: () => (
    <div className="max-w-md">
      <Tabs defaultValue="tab1">
        <TabsList>
          <Tab value="tab1">Overview</Tab>
          <Tab value="tab2">Details</Tab>
          <Tab value="tab3">Activity</Tab>
        </TabsList>
        <TabsPanel value="tab1" className="p-4 text-sm text-[var(--text-primary)]">
          Overview content
        </TabsPanel>
        <TabsPanel value="tab2" className="p-4 text-sm text-[var(--text-primary)]">
          Details content
        </TabsPanel>
        <TabsPanel value="tab3" className="p-4 text-sm text-[var(--text-primary)]">
          Activity content
        </TabsPanel>
      </Tabs>
    </div>
  ),
};

// ============================================================
// Feedback
// ============================================================

const FeedbackMeta = { title: "Feedback" } satisfies Meta;
export { FeedbackMeta };

export const ToastStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <Toast title="Info" description="This is an informational message." variant="info" />
      <Toast title="Success" description="Operation completed successfully." variant="success" />
      <Toast title="Warning" description="Please review before proceeding." variant="warning" />
      <Toast title="Error" description="Something went wrong. Please try again." variant="error" />
    </div>
  ),
};

export const SpinnerStory: StoryObj = {
  render: () => (
    <div className="flex items-center gap-4">
      <Spinner className="h-4 w-4" />
      <Spinner className="h-6 w-6" />
      <Spinner className="h-8 w-8" />
      <Spinner className="h-4 w-4 text-[var(--muhide-orange)]" />
    </div>
  ),
};

export const ModalStory: StoryObj = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Modal>
        <ModalTrigger>
          <Button>Open Modal</Button>
        </ModalTrigger>
        <ModalContent>
          <ModalHeader>Modal Title</ModalHeader>
          <ModalBody>
            <p className="text-sm text-[var(--text-muted)]">
              This is the modal body content. You can put any content here.
            </p>
          </ModalBody>
          <ModalFooter>
            <Button variant="outline">Cancel</Button>
            <Button>Confirm</Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  ),
};

export const TooltipStory: StoryObj = {
  render: () => (
    <div className="flex items-center gap-4 p-8">
      <Tooltip content="This is a tooltip">
        <span className="text-sm text-[var(--text-primary)] underline decoration-dotted cursor-help">
          Hover me
        </span>
      </Tooltip>
    </div>
  ),
};

export const KbdStory: StoryObj = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Kbd>Ctrl</Kbd>
      <Kbd>Shift</Kbd>
      <Kbd>Alt</Kbd>
      <Kbd>Space</Kbd>
      <Kbd>⌘</Kbd>
      <Kbd>K</Kbd>
    </div>
  ),
};

// ============================================================
// Form Layout
// ============================================================

const FormLayoutMeta = { title: "Form Layout" } satisfies Meta;
export { FormLayoutMeta };

export const FormStory: StoryObj = {
  render: () => (
    <Form className="max-w-2xl space-y-6">
      <FormSection label="Basic Information" description="Enter the basic details for this record.">
        <FormRow>
          <FormField label="First Name" required name="firstName">
            <Input placeholder="John" />
          </FormField>
          <FormField label="Last Name" required name="lastName">
            <Input placeholder="Doe" />
          </FormField>
        </FormRow>
        <FormRow>
          <FormField label="Email" required name="email" error="Invalid email address">
            <Input type="email" placeholder="john@acme.com" />
          </FormField>
          <FormField label="Phone" name="phone" helperText="Include country code">
            <Input type="tel" placeholder="+966 50 000 0000" />
          </FormField>
        </FormRow>
      </FormSection>
      <FormSection label="Address">
        <FormRow>
          <FormField label="Street" name="street">
            <Input placeholder="Street address" />
          </FormField>
          <FormField label="City" name="city">
            <Input placeholder="City" />
          </FormField>
        </FormRow>
      </FormSection>
      <FormActions>
        <Button variant="outline" type="button">
          Cancel
        </Button>
        <Button type="submit">Save Changes</Button>
      </FormActions>
    </Form>
  ),
};
