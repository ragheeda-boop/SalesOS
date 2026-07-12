"use client"

import { useState } from "react"
import { Button, Badge, Card, Spinner, Input } from "@salesos/ui"
import { Shield, Plus, Edit3, Trash2, Users, X, Check, Search } from "lucide-react"
import type { RoleManagerViewProps, PermissionItem } from "./types"
import { PERMISSION_GROUP_LABELS } from "./types"

export function RoleManagerView({ roles, permissions, loading, onRefresh, onCreateRole, onUpdateRole, onDeleteRole }: RoleManagerViewProps) {
  const [showCreate, setShowCreate] = useState(false)
  const [editingRole, setEditingRole] = useState<string | null>(null)
  const [editName, setEditName] = useState("")
  const [editDescription, setEditDescription] = useState("")
  const [selectedPerms, setSelectedPerms] = useState<string[]>([])

  const groupedPermissions = permissions.reduce<Record<string, PermissionItem[]>>((acc, p) => {
    const group = p.group || "other"
    if (!acc[group]) acc[group] = []
    acc[group].push(p)
    return acc
  }, {})

  const handleCreate = () => {
    if (!editName.trim()) return
    onCreateRole({ name: editName.trim(), description: editDescription.trim() || undefined, permissions: selectedPerms })
    setShowCreate(false)
    setEditName("")
    setEditDescription("")
    setSelectedPerms([])
  }

  const handleEdit = (role: { id: string; name: string; description: string | null; permissions: string[] }) => {
    setEditingRole(role.id)
    setEditName(role.name)
    setEditDescription(role.description || "")
    setSelectedPerms([...role.permissions])
  }

  const handleSaveEdit = () => {
    if (!editingRole || !editName.trim()) return
    onUpdateRole(editingRole, { name: editName.trim(), description: editDescription.trim() || undefined, permissions: selectedPerms })
    setEditingRole(null)
  }

  const handleCancel = () => {
    setShowCreate(false)
    setEditingRole(null)
    setEditName("")
    setEditDescription("")
    setSelectedPerms([])
  }

  const togglePerm = (key: string) => {
    setSelectedPerms((prev) =>
      prev.includes(key) ? prev.filter((p) => p !== key) : [...prev, key]
    )
  }

  if (loading) {
    return <div className="py-20 text-center text-neutral-500"><Spinner /> جاري التحميل...</div>
  }

  return (
    <div className="space-y-4" role="region" aria-label="إدارة الأدوار">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">إدارة الأدوار والصلاحيات</h2>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={onRefresh}>تحديث</Button>
          <Button onClick={() => { setShowCreate(true); setEditName(""); setEditDescription(""); setSelectedPerms([]) }} className="gap-1">
            <Plus className="h-4 w-4" />دور جديد
          </Button>
        </div>
      </div>

      {/* Create / Edit Form */}
      {(showCreate || editingRole) && (
        <Card className="p-4 space-y-3">
          <h3 className="font-semibold">{editingRole ? "تعديل الدور" : "دور جديد"}</h3>
          <div className="grid grid-cols-2 gap-3">
            <Input
              placeholder="اسم الدور"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
            <Input
              placeholder="وصف (اختياري)"
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
            />
          </div>
          <div>
            <p className="text-sm font-medium mb-2">الصلاحيات</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-60 overflow-y-auto">
              {Object.entries(groupedPermissions).map(([group, perms]) => (
                <div key={group} className="space-y-1">
                  <p className="text-xs font-semibold text-neutral-500">{PERMISSION_GROUP_LABELS[group] || group}</p>
                  {perms.map((p) => (
                    <label
                      key={p.id}
                      className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer text-xs transition ${
                        selectedPerms.includes(p.key) ? "bg-[var(--muhide-orange)]/10 text-[var(--muhide-orange)]" : "hover:bg-neutral-100 dark:hover:bg-neutral-800"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedPerms.includes(p.key)}
                        onChange={() => togglePerm(p.key)}
                        className="rounded border-neutral-300"
                      />
                      <span>{p.name}</span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={editingRole ? handleSaveEdit : handleCreate}>
              {editingRole ? "حفظ" : "إنشاء"}
            </Button>
            <Button variant="ghost" onClick={handleCancel}>إلغاء</Button>
          </div>
        </Card>
      )}

      {/* Roles List */}
      {!roles.length ? (
        <Card className="p-6 text-center text-neutral-500">
          <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>لا توجد أدوار مخصصة</p>
          <p className="text-xs mt-1">الأدوار النظامية غير ظاهرة هنا</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roles.map((role) => (
            <Card key={role.id} className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{role.name}</h3>
                    {role.is_system && <Badge variant="default">نظامي</Badge>}
                  </div>
                  {role.description && (
                    <p className="text-xs text-neutral-500 mt-0.5">{role.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  {!role.is_system && (
                    <>
                      <button
                        onClick={() => handleEdit(role)}
                        className="p-1.5 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800"
                        aria-label={`تعديل ${role.name}`}
                      >
                        <Edit3 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDeleteRole(role.id)}
                        className="p-1.5 rounded hover:bg-danger-50 dark:hover:bg-danger-900/20 text-danger-500"
                        aria-label={`حذف ${role.name}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <Users className="h-3.5 w-3.5" />
                <span>{role.user_count} مستخدم</span>
              </div>

              <div className="flex flex-wrap gap-1">
                {role.permissions.length === 0 ? (
                  <span className="text-xs text-neutral-400">لا توجد صلاحيات</span>
                ) : (
                  role.permissions.slice(0, 8).map((perm) => (
                    <span key={perm} className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 font-mono">
                      {perm}
                    </span>
                  ))
                )}
                {role.permissions.length > 8 && (
                  <span className="text-[10px] text-neutral-400">+{role.permissions.length - 8}</span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
