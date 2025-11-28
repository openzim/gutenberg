export function useMultiSelectFilter<T>(
  props: { modelValue: T[] },
  emit: (event: 'update:modelValue', value: T[]) => void
) {
  function toggle(item: T) {
    const selected = [...props.modelValue]
    const index = selected.indexOf(item)

    if (index > -1) {
      selected.splice(index, 1)
    } else {
      selected.push(item)
    }

    emit('update:modelValue', selected)
  }

  function clearAll() {
    emit('update:modelValue', [])
  }

  function selectAll(allItems: T[]) {
    emit('update:modelValue', [...allItems])
  }

  return { toggle, clearAll, selectAll }
}
