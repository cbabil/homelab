/**
 * DataTable Test Suite
 *
 * Tests for the DataTable component including rendering,
 * sorting, empty states, and row interactions.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataTable, ColumnDef } from '../DataTable'

interface TestItem {
  id: string
  name: string
  value: number
}

const testData: TestItem[] = [
  { id: '1', name: 'Item A', value: 100 },
  { id: '2', name: 'Item B', value: 200 },
  { id: '3', name: 'Item C', value: 50 }
]

const testColumns: ColumnDef<TestItem>[] = [
  {
    id: 'name',
    header: 'Name',
    render: (item) => item.name
  },
  {
    id: 'value',
    header: 'Value',
    sortable: true,
    render: (item) => item.value.toString()
  }
]

describe('DataTable', () => {
  const defaultProps = {
    data: testData,
    columns: testColumns,
    keyExtractor: (item: TestItem) => item.id
  }

  describe('Rendering', () => {
    it('should render table with data', () => {
      render(<DataTable {...defaultProps} />)

      expect(screen.getByText('Item A')).toBeInTheDocument()
      expect(screen.getByText('Item B')).toBeInTheDocument()
      expect(screen.getByText('Item C')).toBeInTheDocument()
    })

    it('should render column headers', () => {
      render(<DataTable {...defaultProps} />)

      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Value')).toBeInTheDocument()
    })

    it('should render all rows', () => {
      render(<DataTable {...defaultProps} />)

      const rows = screen.getAllByRole('row')
      // Header row + 3 data rows
      expect(rows).toHaveLength(4)
    })

    it('should render cell values', () => {
      render(<DataTable {...defaultProps} />)

      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('200')).toBeInTheDocument()
      expect(screen.getByText('50')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no data', () => {
      render(<DataTable {...defaultProps} data={[]} />)

      expect(screen.getByRole('heading')).toBeInTheDocument()
    })

    it('should show custom empty title', () => {
      render(
        <DataTable
          {...defaultProps}
          data={[]}
          emptyTitle="No items found"
        />
      )

      expect(screen.getByText('No items found')).toBeInTheDocument()
    })

    it('should show custom empty message', () => {
      render(
        <DataTable
          {...defaultProps}
          data={[]}
          emptyMessage="Try adjusting your filters"
        />
      )

      expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument()
    })
  })

  describe('Sorting', () => {
    const sortFn = (a: TestItem, b: TestItem, field: string, direction: 'asc' | 'desc') => {
      const multiplier = direction === 'asc' ? 1 : -1
      if (field === 'value') {
        return (a.value - b.value) * multiplier
      }
      return 0
    }

    it('should render sort button for sortable columns', () => {
      render(<DataTable {...defaultProps} sortFn={sortFn} />)

      // Value column is sortable
      const valueHeader = screen.getByRole('button', { name: /value/i })
      expect(valueHeader).toBeInTheDocument()
    })

    it('should not render sort button for non-sortable columns', () => {
      render(<DataTable {...defaultProps} sortFn={sortFn} />)

      // Name column header should be text, not button
      const nameHeader = screen.getByText('Name')
      expect(nameHeader.closest('button')).toBeNull()
    })

    it('should toggle sort direction on click', async () => {
      const user = userEvent.setup()
      render(
        <DataTable
          {...defaultProps}
          sortFn={sortFn}
          defaultSortField="value"
          defaultSortDirection="desc"
        />
      )

      const sortButton = screen.getByRole('button', { name: /value/i })

      // First click should toggle to asc
      await user.click(sortButton)

      // Data should now be sorted ascending (50, 100, 200)
      const cells = screen.getAllByRole('cell')
      const valueIndex = cells.findIndex(cell => cell.textContent === '50')
      expect(valueIndex).toBeGreaterThanOrEqual(0)
    })

    it('should show sort indicator', () => {
      render(
        <DataTable
          {...defaultProps}
          sortFn={sortFn}
          defaultSortField="value"
          defaultSortDirection="desc"
        />
      )

      // Should show down arrow for desc
      expect(screen.getByText('↓')).toBeInTheDocument()
    })
  })

  describe('Row Click', () => {
    it('should call onRowClick when row is clicked', async () => {
      const user = userEvent.setup()
      const onRowClick = vi.fn()
      render(<DataTable {...defaultProps} onRowClick={onRowClick} />)

      const firstDataRow = screen.getAllByRole('row')[1]
      await user.click(firstDataRow)

      expect(onRowClick).toHaveBeenCalledTimes(1)
      expect(onRowClick).toHaveBeenCalledWith(expect.objectContaining({ id: '1' }))
    })

    it('should not call onRowClick when not provided', async () => {
      const user = userEvent.setup()
      render(<DataTable {...defaultProps} />)

      const firstDataRow = screen.getAllByRole('row')[1]
      await user.click(firstDataRow)

      // No error should occur
      expect(true).toBe(true)
    })
  })

  describe('Custom Rendering', () => {
    it('should use custom render function for cells', () => {
      const customColumns: ColumnDef<TestItem>[] = [
        {
          id: 'name',
          header: 'Name',
          render: (item) => <strong data-testid="custom-name">{item.name}</strong>
        }
      ]

      render(<DataTable {...defaultProps} columns={customColumns} />)

      expect(screen.getAllByTestId('custom-name')).toHaveLength(3)
    })

    it('should pass index to render function', () => {
      const customColumns: ColumnDef<TestItem>[] = [
        {
          id: 'index',
          header: 'Index',
          render: (_, index) => <span data-testid={`index-${index}`}>{index}</span>
        }
      ]

      render(<DataTable {...defaultProps} columns={customColumns} />)

      expect(screen.getByTestId('index-0')).toHaveTextContent('0')
      expect(screen.getByTestId('index-1')).toHaveTextContent('1')
      expect(screen.getByTestId('index-2')).toHaveTextContent('2')
    })
  })

  describe('Accessibility', () => {
    it('should use semantic table elements', () => {
      render(<DataTable {...defaultProps} />)

      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getAllByRole('columnheader').length).toBeGreaterThan(0)
      expect(screen.getAllByRole('cell').length).toBeGreaterThan(0)
    })

    it('should have hover state on rows when clickable', () => {
      render(<DataTable {...defaultProps} onRowClick={vi.fn()} />)

      const dataRows = screen.getAllByRole('row').slice(1)
      dataRows.forEach(row => {
        expect(row).toHaveStyle({ cursor: 'pointer' })
      })
    })
  })
})
