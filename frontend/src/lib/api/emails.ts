/**
 * Emails/Invoices API endpoints for managing Gmail invoices
 */

import { api, type ApiResponse } from './client';

export interface Invoice {
	id: number;
	gmail_id: string;
	sender: string;
	subject: string;
	category: string;
	label: string;
	amount: number | null;
	currency: string;
	date_received: string;
	date_processed: string;
	due_date: string | null;
	is_paid: boolean;
	has_attachment: boolean;
	calendar_event_id: string | null;
}

export interface InvoiceStats {
	categories: {
		category: string;
		count: number;
		unpaid_count: number;
		paid_count: number;
		unpaid_amount: number | null;
		paid_amount: number | null;
	}[];
	totals: {
		total_invoices: number;
		unpaid_count: number;
		paid_count: number;
		unpaid_amount: number;
		paid_amount: number;
	};
}

export interface InvoiceTodo {
	id: number;
	title: string;
	description: string;
	category: string;
	priority: 'urgent' | 'high' | 'normal';
	due_date: string | null;
	amount: number | null;
	source: string;
	source_id: string;
	status: 'pending' | 'completed' | 'cancelled';
	created_at: string;
	completed_at: string | null;
}

export interface OnepageEmail {
	id: number;
	gmail_id: string;
	subject: string;
	date_received: string;
	file_path: string;
	date_processed: string;
}

export interface ProcessingLog {
	id: number;
	timestamp: string;
	emails_scanned: number;
	invoices_found: number;
	onepage_found: number;
	calendar_events_created: number;
	errors: string[];
}

// ============================================================================
// Invoices
// ============================================================================

/**
 * Get all invoices with optional filtering
 */
export async function getInvoices(
	category?: string,
	isPaid?: boolean,
	limit = 50,
	offset = 0
): Promise<ApiResponse<Invoice[]>> {
	const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
	if (category) params.set('category', category);
	if (isPaid !== undefined) params.set('is_paid', String(isPaid));
	return api.get<Invoice[]>(`/api/v1/emails?${params}`);
}

/**
 * Get invoice statistics
 */
export async function getInvoiceStats(): Promise<ApiResponse<InvoiceStats>> {
	return api.get<InvoiceStats>('/api/v1/emails/stats');
}

/**
 * Get upcoming invoice due dates
 */
export async function getUpcomingDueDates(limit = 10): Promise<ApiResponse<Invoice[]>> {
	return api.get<Invoice[]>(`/api/v1/emails/upcoming?limit=${limit}`);
}

/**
 * Mark an invoice as paid
 */
export async function markInvoicePaid(
	invoiceId: number
): Promise<ApiResponse<{ success: boolean; invoice_id: number }>> {
	return api.post<{ success: boolean; invoice_id: number }>(
		`/api/v1/emails/${invoiceId}/mark-paid`
	);
}

// ============================================================================
// Todos
// ============================================================================

/**
 * Get invoice-related todos
 */
export async function getInvoiceTodos(
	status?: string,
	limit = 50
): Promise<ApiResponse<InvoiceTodo[]>> {
	const params = new URLSearchParams({ limit: String(limit) });
	if (status) params.set('status_filter', status);
	return api.get<InvoiceTodo[]>(`/api/v1/emails/todos?${params}`);
}

/**
 * Update todo status
 */
export async function updateTodoStatus(
	todoId: number,
	status: 'pending' | 'completed' | 'cancelled'
): Promise<ApiResponse<InvoiceTodo>> {
	return api.patch<InvoiceTodo>(`/api/v1/emails/todos/${todoId}`, { status });
}

// ============================================================================
// One Page (Trading)
// ============================================================================

/**
 * Get One Page trading emails
 */
export async function getOnepageEmails(limit = 20): Promise<ApiResponse<OnepageEmail[]>> {
	return api.get<OnepageEmail[]>(`/api/v1/emails/onepage?limit=${limit}`);
}

// ============================================================================
// Processing
// ============================================================================

/**
 * Get processing logs
 */
export async function getProcessingLogs(limit = 10): Promise<ApiResponse<ProcessingLog[]>> {
	return api.get<ProcessingLog[]>(`/api/v1/emails/logs?limit=${limit}`);
}

/**
 * Manually run the email sorter
 */
export async function runEmailSorter(): Promise<
	ApiResponse<{ success: boolean; output: string; timestamp: string }>
> {
	return api.post<{ success: boolean; output: string; timestamp: string }>(
		'/api/v1/emails/run-sorter'
	);
}

/**
 * Check email service health
 */
export async function checkEmailServiceHealth(): Promise<
	ApiResponse<{ available: boolean; host: string; service: string }>
> {
	return api.get<{ available: boolean; host: string; service: string }>('/api/v1/emails/health');
}
