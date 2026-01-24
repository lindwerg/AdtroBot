import { type Page, type Locator, expect } from '@playwright/test';

/**
 * Page Object Model for the Monitoring page.
 * Displays API costs, active users, and unit economics with charts.
 */
export class MonitoringPage {
  readonly page: Page;
  readonly title: Locator;
  readonly dateFilter: Locator;
  readonly dauCard: Locator;
  readonly wauCard: Locator;
  readonly mauCard: Locator;
  readonly totalCostCard: Locator;
  readonly totalTokensCard: Locator;
  readonly requestsCard: Locator;
  readonly avgCostCard: Locator;
  readonly costChartCard: Locator;
  readonly operationsCard: Locator;
  readonly areaChart: Locator;
  readonly barChart: Locator;
  readonly operationsTable: Locator;
  readonly errorAlert: Locator;

  constructor(page: Page) {
    this.page = page;
    this.title = page.getByRole('heading', { name: /мониторинг/i });
    this.dateFilter = page.locator('.ant-segmented');
    this.dauCard = page.locator('.ant-card').filter({ hasText: /DAU/ }).first();
    this.wauCard = page.locator('.ant-card').filter({ hasText: /WAU/ });
    this.mauCard = page.locator('.ant-card').filter({ hasText: /MAU/ });
    this.totalCostCard = page.locator('.ant-card').filter({ hasText: /общая стоимость/i });
    this.totalTokensCard = page.locator('.ant-card').filter({ hasText: /всего токенов/i });
    this.requestsCard = page.locator('.ant-card').filter({ hasText: /запросов/i }).first();
    this.avgCostCard = page.locator('.ant-card').filter({ hasText: /средняя стоимость/i });
    this.costChartCard = page.locator('.ant-card').filter({ hasText: /стоимость по дням/i });
    this.operationsCard = page.locator('.ant-card').filter({ hasText: /стоимость по операциям/i });
    this.areaChart = page.locator('.recharts-area');
    this.barChart = page.locator('.recharts-bar');
    this.operationsTable = this.operationsCard.locator('.ant-table');
    this.errorAlert = page.locator('.ant-alert-error');
  }

  /**
   * Navigate to the monitoring page.
   */
  async goto() {
    await this.page.goto('/monitoring');
    await expect(this.title).toBeVisible();
  }

  /**
   * Wait for page to fully load with data.
   */
  async waitForLoad() {
    await expect(this.title).toBeVisible();
    await this.page.waitForLoadState('networkidle');
    // Wait for at least one statistic to show
    await expect(this.dauCard).toBeVisible();
  }

  /**
   * Select a date range from the filter.
   * @param range - '24h' | '7d' | '30d'
   */
  async selectDateRange(range: '24h' | '7d' | '30d') {
    const labels: Record<string, string> = {
      '24h': '24 часа',
      '7d': '7 дней',
      '30d': '30 дней',
    };
    await this.dateFilter.getByText(labels[range]).click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for charts to render.
   */
  async waitForCharts() {
    await expect(this.costChartCard).toBeVisible();
    // Wait for recharts to render (SVG elements)
    await this.page.waitForSelector('.recharts-responsive-container', { state: 'visible' });
  }

  /**
   * Check if area chart is visible.
   */
  async hasAreaChart(): Promise<boolean> {
    try {
      await this.areaChart.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if bar chart is visible.
   */
  async hasBarChart(): Promise<boolean> {
    try {
      await this.barChart.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get DAU value from card.
   */
  async getDAU(): Promise<string> {
    const stat = this.dauCard.locator('.ant-statistic-content-value');
    return await stat.textContent() ?? '0';
  }

  /**
   * Get total cost value.
   */
  async getTotalCost(): Promise<string> {
    const stat = this.totalCostCard.locator('.ant-statistic-content-value');
    return await stat.textContent() ?? '$0';
  }

  /**
   * Get operations count from table.
   */
  async getOperationsCount(): Promise<number> {
    const rows = this.operationsTable.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Check if error state is displayed.
   */
  async hasError(): Promise<boolean> {
    return await this.errorAlert.isVisible();
  }
}
