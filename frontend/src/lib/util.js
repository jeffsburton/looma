export function getLocaleDateFormat(){
  // Get the locale's date format parts
  const formatter = new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })

  const parts = formatter.formatToParts(new Date(2023, 0, 15))

  // Build format string based on the order of parts
  let format = ''
  for (const part of parts) {
    switch (part.type) {
      case 'year':
        format += 'yy'
        break
      case 'month':
        format += 'mm'
        break
      case 'day':
        format += 'dd'
        break
      case 'literal':
        format += part.value
        break
    }
  }

  return format
}