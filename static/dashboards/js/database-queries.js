// Database Dashboard JavaScript
class DatabaseDashboard {
    constructor() {
        this.currentQuery = '';
        this.queryHistory = [];
        this.savedQueries = [];
        this.init();
    }

    init() {
        this.loadSavedQueries();
        this.loadVersionInfo();
        this.setupEventListeners();
        this.loadQueryHistory();
    }

    setupEventListeners() {
        // Quick query buttons
        document.querySelectorAll('.quick-query-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.executeQuickQuery(e.target.dataset.query);
                this.setActiveQuickQuery(e.target);
            });
        });

        // Enter key in textarea
        document.getElementById('natural-query-input').addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.executeNaturalQuery();
            }
        });
    }

    setActiveQuickQuery(activeBtn) {
        document.querySelectorAll('.quick-query-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        activeBtn.classList.add('active');
    }

    async loadVersionInfo() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            document.getElementById('version-info').textContent = `v${data.version || 'Unknown'}`;
        } catch (error) {
            console.error('Failed to load version:', error);
        }
    }

    async loadSavedQueries() {
        try {
            const response = await fetch('/api/v1/dashboards/database/queries/saved');
            const data = await response.json();
            this.savedQueries = data.queries || [];
            this.renderSavedQueries();
        } catch (error) {
            console.error('Failed to load saved queries:', error);
            document.getElementById('saved-queries-list').innerHTML = 
                '<p style="color: #ef4444; font-size: 0.9rem;">Failed to load saved queries</p>';
        }
    }

    renderSavedQueries() {
        const container = document.getElementById('saved-queries-list');
        
        if (this.savedQueries.length === 0) {
            container.innerHTML = '<p style="color: #6b7280; font-size: 0.9rem;">No saved queries</p>';
            return;
        }

        container.innerHTML = this.savedQueries.map(query => `
            <div class="history-item" onclick="dashboard.loadSavedQuery('${query.id}')">
                <div class="history-query" style="font-weight: 500;">${query.query_name}</div>
                <div class="history-time">Used ${query.use_count || 0} times</div>
            </div>
        `).join('');
    }

    async loadSavedQuery(queryId) {
        try {
            const query = this.savedQueries.find(q => q.id == queryId);
            if (query) {
                document.getElementById('natural-query-input').value = query.sql_query;
                await this.executeDirectSQL(query.sql_query);
                
                // Update use count
                await fetch(`/api/v1/dashboards/database/queries/saved/${queryId}/use`, {
                    method: 'POST'
                });
            }
        } catch (error) {
            console.error('Failed to load saved query:', error);
        }
    }

    loadQueryHistory() {
        const history = localStorage.getItem('ava-query-history');
        if (history) {
            this.queryHistory = JSON.parse(history);
            this.renderQueryHistory();
        }
    }

    saveToHistory(query, type = 'natural') {
        const historyItem = {
            query: query,
            type: type,
            timestamp: Date.now()
        };
        
        this.queryHistory.unshift(historyItem);
        this.queryHistory = this.queryHistory.slice(0, 10); // Keep last 10
        
        localStorage.setItem('ava-query-history', JSON.stringify(this.queryHistory));
        this.renderQueryHistory();
    }

    renderQueryHistory() {
        const container = document.getElementById('query-history');
        
        if (this.queryHistory.length === 0) {
            container.innerHTML = '<p style="color: #6b7280; text-align: center;">No queries yet</p>';
            return;
        }

        container.innerHTML = this.queryHistory.map((item, index) => `
            <div class="history-item" onclick="dashboard.rerunHistoryQuery(${index})">
                <div class="history-query">${this.truncateText(item.query, 60)}</div>
                <div class="history-time">${this.formatTime(item.timestamp)}</div>
            </div>
        `).join('');
    }

    async rerunHistoryQuery(index) {
        const item = this.queryHistory[index];
        document.getElementById('natural-query-input').value = item.query;
        
        if (item.type === 'natural') {
            await this.executeNaturalQuery();
        } else {
            await this.executeDirectSQL(item.query);
        }
    }

    async executeQuickQuery(queryType) {
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/v1/dashboards/database/queries/quick/${queryType}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data.results, data.sql_query, data.execution_time);
                this.saveToHistory(data.description || queryType, 'quick');
            } else {
                this.showError(data.error || 'Quick query failed');
            }
        } catch (error) {
            console.error('Quick query error:', error);
            this.showError('Failed to execute quick query');
        } finally {
            this.showLoading(false);
        }
    }

    async executeNaturalQuery() {
        const query = document.getElementById('natural-query-input').value.trim();
        
        if (!query) {
            this.showError('Please enter a question');
            return;
        }

        this.showLoading(true);
        this.currentQuery = query;
        
        try {
            const response = await fetch('/api/v1/dashboards/database/query/natural', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: query })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayGeneratedSQL(data.sql_query);
                this.displayResults(data.results, data.sql_query, data.execution_time);
                this.saveToHistory(query, 'natural');
                this.showSuccess(`Query executed successfully. ${data.results.length} rows returned.`);
            } else {
                this.showError(data.error || 'Failed to process natural language query');
            }
        } catch (error) {
            console.error('Natural query error:', error);
            this.showError('Failed to execute query. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    async executeDirectSQL(sqlQuery) {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/v1/dashboards/database/query/direct', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sql_query: sqlQuery })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayGeneratedSQL(sqlQuery);
                this.displayResults(data.results, sqlQuery, data.execution_time);
                this.saveToHistory(sqlQuery, 'direct');
                this.showSuccess(`Query executed successfully. ${data.results.length} rows returned.`);
            } else {
                this.showError(data.error || 'Failed to execute SQL query');
            }
        } catch (error) {
            console.error('Direct SQL error:', error);
            this.showError('Failed to execute query. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    displayGeneratedSQL(sqlQuery) {
        document.getElementById('generated-sql').textContent = sqlQuery;
        document.getElementById('sql-section').style.display = 'block';
    }

    displayResults(results, sqlQuery, executionTime) {
        const container = document.getElementById('query-results');
        const section = document.getElementById('results-section');
        
        if (!results || results.length === 0) {
            container.innerHTML = '<p style="color: #6b7280; text-align: center;">No results found</p>';
            section.style.display = 'block';
            return;
        }

        // Display query stats
        document.getElementById('execution-time').textContent = `${executionTime}ms`;
        document.getElementById('rows-returned').textContent = results.length;
        document.getElementById('query-cost').textContent = 'Low';
        document.getElementById('query-stats').style.display = 'flex';

        // Check if this is a farmers table query to add delete buttons
        const isFarmersQuery = sqlQuery && sqlQuery.toLowerCase().includes('farmers');
        const hasId = results[0] && (results[0].id !== undefined || results[0].farmer_id !== undefined);
        const showDelete = isFarmersQuery && hasId;

        // Create table
        const columns = Object.keys(results[0]);
        const tableHTML = `
            <div class="results-table">
                <table class="table">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${this.formatColumnName(col)}</th>`).join('')}
                            ${showDelete ? '<th style="text-align: center;">Actions</th>' : ''}
                        </tr>
                    </thead>
                    <tbody>
                        ${results.map(row => `
                            <tr>
                                ${columns.map(col => `<td>${this.formatCellValue(row[col])}</td>`).join('')}
                                ${showDelete ? `
                                    <td style="text-align: center;">
                                        <button class="btn btn-danger btn-sm" onclick="dashboard.confirmDelete('farmers', ${row.id || row.farmer_id}, '${(row.manager_name || row.first_name || '')} ${(row.manager_last_name || row.last_name || '')}')">
                                            🔒 Deactivate
                                        </button>
                                    </td>
                                ` : ''}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        section.style.display = 'block';
    }

    async confirmDelete(table, id, displayName) {
        // Create confirmation dialog
        const confirmed = confirm(`⚠️ WARNING: Are you sure you want to deactivate this farmer?\n\nTable: ${table}\nID: ${id}\nName: ${displayName}\n\nThe farmer will be marked as inactive.`);
        
        if (!confirmed) {
            return;
        }
        
        // Second confirmation for extra safety
        const reallyConfirmed = confirm(`🔴 FINAL CONFIRMATION\n\nYou are about to deactivate:\n${displayName} (ID: ${id})\n\nAre you absolutely sure?`);
        
        if (!reallyConfirmed) {
            return;
        }
        
        // Execute deactivation (set is_active = false instead of deleting)
        this.showLoading(true);
        try {
            const deactivateQuery = `UPDATE ${table} SET is_active = false WHERE id = ${id}`;
            const response = await fetch('/api/v1/dashboards/database/query/direct', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sql_query: deactivateQuery })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(`Farmer deactivated successfully (ID: ${id})`);
                // Refresh the current query after deactivation
                const lastQueryBtn = document.querySelector('.quick-query-btn.active');
                if (lastQueryBtn) {
                    lastQueryBtn.click();
                }
            } else {
                this.showError(`Failed to deactivate farmer: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            this.showError(`Delete failed: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    formatColumnName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatCellValue(value) {
        if (value === null || value === undefined) {
            return '<span style="color: #9ca3af;">null</span>';
        }
        
        if (typeof value === 'boolean') {
            return value ? '✓' : '✗';
        }
        
        if (typeof value === 'number') {
            return value.toLocaleString();
        }
        
        if (typeof value === 'string' && value.length > 100) {
            return `<span title="${value}">${value.substring(0, 100)}...</span>`;
        }
        
        return value;
    }

    showLoading(show) {
        const section = document.getElementById('results-section');
        if (show) {
            section.classList.add('loading');
        } else {
            section.classList.remove('loading');
        }
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showMessage(message, type) {
        const container = document.getElementById('message-container');
        const alertClass = type === 'error' ? 'error-message' : 'success-message';
        
        container.innerHTML = `
            <div class="${alertClass}">
                ${message}
                <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 1.2rem; cursor: pointer;">×</button>
            </div>
        `;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector(`.${alertClass}`);
            if (alert) alert.remove();
        }, 5000);
    }

    clearQuery() {
        document.getElementById('natural-query-input').value = '';
        document.getElementById('sql-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('message-container').innerHTML = '';
        
        // Clear active quick query
        document.querySelectorAll('.quick-query-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }

    async exportResults() {
        // Simple CSV export for now
        const table = document.querySelector('.results-table table');
        if (!table) {
            this.showError('No results to export');
            return;
        }

        let csv = '';
        
        // Headers
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
        csv += headers.join(',') + '\n';
        
        // Rows
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('td')).map(td => {
                const text = td.textContent.replace(/"/g, '""');
                return `"${text}"`;
            });
            csv += cells.join(',') + '\n';
        });
        
        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ava-query-results-${Date.now()}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        this.showSuccess('Results exported to CSV file');
    }

    truncateText(text, maxLength) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
    }
}

// Save Query Functions (called from HTML)
function showSaveQueryDialog() {
    if (!dashboard.currentQuery) {
        dashboard.showError('No query to save');
        return;
    }
    document.getElementById('save-query-modal').style.display = 'block';
}

function hideSaveQueryDialog() {
    document.getElementById('save-query-modal').style.display = 'none';
    document.getElementById('save-query-name').value = '';
}

async function saveQuery() {
    const name = document.getElementById('save-query-name').value.trim();
    const sql = document.getElementById('generated-sql').textContent;
    
    if (!name) {
        dashboard.showError('Please enter a query name');
        return;
    }
    
    if (!sql) {
        dashboard.showError('No SQL query to save');
        return;
    }

    try {
        const response = await fetch('/api/v1/dashboards/database/queries/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query_name: name,
                sql_query: sql
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            dashboard.showSuccess('Query saved successfully');
            hideSaveQueryDialog();
            dashboard.loadSavedQueries();
        } else {
            dashboard.showError(data.error || 'Failed to save query');
        }
    } catch (error) {
        console.error('Save query error:', error);
        dashboard.showError('Failed to save query');
    }
}

// Global functions for inline event handlers
function executeNaturalQuery() {
    dashboard.executeNaturalQuery();
}

function clearQuery() {
    dashboard.clearQuery();
}

function exportResults() {
    dashboard.exportResults();
}

// Initialize dashboard
const dashboard = new DatabaseDashboard();