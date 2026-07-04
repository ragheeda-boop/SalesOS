import { useForm, type UseFormProps, type UseFormReturn, type FieldValues, type Path } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { createElement } from 'react'

export type FieldType = 'string' | 'number' | 'boolean' | 'email' | 'url' | 'date' | 'enum' | 'textarea'

export interface FormFieldDefinition {
  name: string
  type: FieldType
  label: string
  placeholder?: string
  required?: boolean
  minLength?: number
  maxLength?: number
  minimum?: number
  maximum?: number
  pattern?: string
  options?: { label: string; value: string }[]
  defaultValue?: unknown
  order?: number
  width?: 'full' | 'half' | 'third'
  section?: string
  visibility?: string
}

export interface FormDefinition {
  title: string
  description?: string
  fields: FormFieldDefinition[]
  submitLabel?: string
}

export interface FormErrors {
  [key: string]: string
}

function buildZodSchema(fields: FormFieldDefinition[]): z.ZodObject<any> {
  const shape: Record<string, z.ZodTypeAny> = {}
  for (const field of fields) {
    let schema: z.ZodTypeAny
    switch (field.type) {
      case 'string':
      case 'textarea':
        schema = z.string()
        if (field.minLength) schema = (schema as z.ZodString).min(field.minLength)
        if (field.maxLength) schema = (schema as z.ZodString).max(field.maxLength)
        if (field.pattern) schema = (schema as z.ZodString).regex(new RegExp(field.pattern))
        break
      case 'number':
        schema = z.coerce.number()
        if (field.minimum !== undefined) schema = (schema as z.ZodNumber).min(field.minimum)
        if (field.maximum !== undefined) schema = (schema as z.ZodNumber).max(field.maximum)
        break
      case 'boolean':
        schema = z.boolean()
        break
      case 'email':
        schema = z.string().email()
        break
      case 'url':
        schema = z.string().url()
        break
      case 'date':
        schema = z.string()
        break
      case 'enum':
        schema = z.enum(field.options?.map((o) => o.value) as [string, ...string[]] || [''])
        break
      default:
        schema = z.string()
    }
    if (field.required) {
      shape[field.name] = schema
    } else {
      shape[field.name] = schema.optional().or(z.literal(''))
    }
  }
  return z.object(shape)
}

function fieldToDefault(field: FormFieldDefinition): unknown {
  if (field.defaultValue !== undefined) return field.defaultValue
  switch (field.type) {
    case 'boolean': return false
    case 'number': return undefined
    default: return ''
  }
}

export function useFormFromDefinition<T extends FieldValues>(
  formDef: FormDefinition,
  options?: Omit<UseFormProps<T>, 'resolver'>
): UseFormReturn<T> {
  const zodSchema = buildZodSchema(formDef.fields) as unknown as z.ZodType<T>
  const defaults = formDef.fields.reduce((acc: Record<string, unknown>, f) => {
    acc[f.name] = fieldToDefault(f)
    return acc
  }, {})

  return useForm({
    resolver: zodResolver(zodSchema),
    defaultValues: defaults as any,
    ...options,
  }) as UseFormReturn<T>
}

export function FormField({
  field,
  register,
  error,
}: {
  field: FormFieldDefinition
  register: any
  error?: string
}) {
  const baseClasses =
    'w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500'

  const errorClasses = error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''

  switch (field.type) {
    case 'textarea':
      return (
        <textarea
          {...register(field.name)}
          placeholder={field.placeholder}
          className={`${baseClasses} ${errorClasses} min-h-[80px]`}
          rows={3}
        />
      )
    case 'boolean':
      return (
        <input
          type="checkbox"
          {...register(field.name)}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      )
    case 'enum':
      return (
        <select {...register(field.name)} className={`${baseClasses} ${errorClasses}`}>
          {field.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )
    case 'number':
      return (
        <input
          type="number"
          {...register(field.name, { valueAsNumber: true })}
          placeholder={field.placeholder}
          className={`${baseClasses} ${errorClasses}`}
        />
      )
    default:
      return (
        <input
          type={field.type === 'email' ? 'email' : field.type === 'url' ? 'url' : field.type === 'date' ? 'date' : 'text'}
          {...register(field.name)}
          placeholder={field.placeholder}
          className={`${baseClasses} ${errorClasses}`}
        />
      )
  }
}

export function FormRenderer({
  definition,
  form,
  onSubmit,
  errors,
}: {
  definition: FormDefinition
  form: UseFormReturn<any>
  onSubmit: (data: any) => void
  errors?: FormErrors
}) {
  const sortedFields = [...definition.fields].sort((a, b) => (a.order ?? 0) - (b.order ?? 0))

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {definition.title && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{definition.title}</h2>
          {definition.description && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{definition.description}</p>
          )}
        </div>
      )}
      <div className="space-y-4">
        {sortedFields.map((field) => {
          const fieldError = errors?.[field.name] || form.formState.errors[field.name]?.message?.toString()
          return (
            <div key={field.name}>
              <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                {field.label}
                {field.required && <span className="ml-1 text-red-500">*</span>}
              </label>
              <FormField field={field} register={form.register} error={fieldError} />
              {fieldError && <p className="mt-1 text-xs text-red-500">{fieldError}</p>}
            </div>
          )
        })}
      </div>
      <button
        type="submit"
        className="inline-flex h-10 items-center justify-center rounded-lg bg-blue-600 px-6 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
      >
        {definition.submitLabel || 'Submit'}
      </button>
    </form>
  )
}
