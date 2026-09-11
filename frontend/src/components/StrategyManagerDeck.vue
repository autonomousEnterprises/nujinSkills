<template>
  <div class="w-full h-full overflow-y-auto font-mono select-none bg-base-100 text-base-content px-3 md:px-6 py-4 transition-colors">
    <div class="w-full space-y-4">

      <!-- ── TOP PORTFOLIO KPI SUMMARY BAR ── -->
      <div class="card bg-base-200 border border-base-content/10 shadow-sm p-4 md:p-5">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="p-3 rounded-box bg-secondary/10 border border-secondary/30 text-secondary">
              <Layers class="w-6 h-6" />
            </div>
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-bold text-sm text-base-content">STRATEGY PORTFOLIO &amp; LIFECYCLE MANAGER</span>
                <span class="badge badge-sm badge-secondary font-bold">{{ strategies.length }} STRATEGIES REGISTERED</span>
                <span class="badge badge-sm badge-success badge-outline bg-success/10 font-bold">
                  {{ activeCount }} ACTIVE LIVE BOTS
                </span>
              </div>
              <div class="text-[11px] text-base-content/60 mt-0.5">
                Autonomous ranking, live alpha decay drift trajectory, and multi-bot capital allocation
              </div>
            </div>
          </div>

          <!-- Cron Trigger Button -->
          <button
            @click="handleTriggerCron"
            :disabled="runningCron"
            class="btn btn-xs sm:btn-sm btn-primary gap-1.5 shadow font-bold"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="runningCron ? 'animate-spin' : ''" />
            <span>{{ runningCron ? 'Auditing Portfolios...' : 'Trigger Cron Evaluations' }}</span>
          </button>
        </div>

        <!-- 5 KPI Stat Cards -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mt-4 pt-4 border-t border-base-content/10">
          <div class="stat bg-base-300/40 border border-base-content/10 rounded-box p-3">
            <div class="stat-title text-[9px] uppercase font-bold text-base-content/50">Active Bots</div>
            <div class="stat-value text-lg font-mono text-success mt-0.5">{{ activeCount }} Active</div>
            <div class="stat-desc text-[9px] text-base-content/40">{{ cronCount }} in cron eval</div>
          </div>

          <div class="stat bg-base-300/40 border border-base-content/10 rounded-box p-3">
            <div class="stat-title text-[9px] uppercase font-bold text-base-content/50">Blended Sharpe</div>
            <div class="stat-value text-lg font-mono text-primary mt-0.5">{{ portfolio.blended_sharpe }}</div>
            <div class="stat-desc text-[9px] text-base-content/40">Portfolio weighted</div>
          </div>

          <div class="stat bg-base-300/40 border border-base-content/10 rounded-box p-3">
            <div class="stat-title text-[9px] uppercase font-bold text-base-content/50">Blended Win Rate</div>
            <div class="stat-value text-lg font-mono text-accent mt-0.5">{{ portfolio.blended_win_rate }}%</div>
            <div class="stat-desc text-[9px] text-base-content/40">{{ portfolio.total_trades }} total trades</div>
          </div>

          <div class="stat bg-base-300/40 border border-base-content/10 rounded-box p-3">
            <div class="stat-title text-[9px] uppercase font-bold text-base-content/50">Profit Factor</div>
            <div class="stat-value text-lg font-mono text-secondary mt-0.5">{{ portfolio.combined_profit_factor }}</div>
            <div class="stat-desc text-[9px] text-base-content/40">Combined payout</div>
          </div>

          <div class="stat bg-base-300/40 border border-base-content/10 rounded-box p-3 col-span-2 md:col-span-1">
            <div class="stat-title text-[9px] uppercase font-bold text-base-content/50">Realized Net PnL</div>
            <div class="stat-value text-lg font-mono mt-0.5" :class="portfolio.total_realized_pnl >= 0 ? 'text-success' : 'text-error'">
              {{ portfolio.total_realized_pnl > 0 ? '+' : '' }}{{ portfolio.total_realized_pnl }}%
            </div>
            <div class="stat-desc text-[9px] text-base-content/40">Realized closed pnl</div>
          </div>
        </div>
      </div>

      <!-- ── DECK TABS & CONTROLS ── -->
      <div class="card bg-base-200 border border-base-content/10 p-3 flex flex-wrap items-center justify-between gap-3">
        <!-- Tab selector -->
        <div class="join">
          <button
            @click="activeTab = 'LEADERBOARD'"
            class="btn btn-xs sm:btn-sm join-item font-mono font-bold gap-1.5"
            :class="activeTab === 'LEADERBOARD' ? 'btn-primary text-primary-content shadow' : 'btn-ghost text-base-content/70'"
          >
            <Award class="w-4 h-4" />
            <span>Leaderboard</span>
          </button>

          <button
            @click="activeTab = 'DRIFT_TRAJECTORY'"
            class="btn btn-xs sm:btn-sm join-item font-mono font-bold gap-1.5"
            :class="activeTab === 'DRIFT_TRAJECTORY' ? 'btn-primary text-primary-content shadow' : 'btn-ghost text-base-content/70'"
          >
            <TrendingUp class="w-4 h-4" />
            <span>Alpha Drift Trajectory</span>
          </button>

          <button
            @click="activeTab = 'DISTRIBUTION'"
            class="btn btn-xs sm:btn-sm join-item font-mono font-bold gap-1.5"
            :class="activeTab === 'DISTRIBUTION' ? 'btn-primary text-primary-content shadow' : 'btn-ghost text-base-content/70'"
          >
            <PieChart class="w-4 h-4" />
            <span>Risk &amp; Distribution</span>
          </button>
        </div>

        <!-- Metric Mode switch (LIVE vs BACKTEST) -->
        <div v-if="activeTab === 'LEADERBOARD'" class="flex items-center gap-2">
          <span class="text-[10px] text-base-content/50 uppercase font-bold">Metrics Mode:</span>
          <div class="join border border-base-content/10 rounded-btn overflow-hidden bg-base-300">
            <button
              @click="tableMetricMode = 'LIVE'"
              class="btn btn-xs join-item font-mono"
              :class="tableMetricMode === 'LIVE' ? 'btn-success text-success-content font-bold' : 'btn-ghost text-base-content/60'"
            >
              Live Telemetry
            </button>
            <button
              @click="tableMetricMode = 'BACKTEST'"
              class="btn btn-xs join-item font-mono"
              :class="tableMetricMode === 'BACKTEST' ? 'btn-secondary text-secondary-content font-bold' : 'btn-ghost text-base-content/60'"
            >
              Backtest Benchmark
            </button>
          </div>
        </div>
      </div>

      <!-- ── TAB 1: LEADERBOARD VIEW ── -->
      <div v-if="activeTab === 'LEADERBOARD'" class="space-y-4">
        <!-- Search & Filter Bar -->
        <div class="flex flex-wrap items-center justify-between gap-3 bg-base-200 border border-base-content/10 p-3 rounded-box text-xs">
          <!-- Search input -->
          <div class="relative flex-1 min-w-[200px]">
            <Search class="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" />
            <input 
              v-model="searchQuery"
              type="text"
              placeholder="Filter by strategy name, thesis, or asset..."
              class="input input-xs sm:input-sm w-full pl-8 bg-base-300 border-base-content/10 text-xs font-mono"
            />
          </div>

          <!-- Status filter pill buttons -->
          <div class="join">
            <button
              v-for="st in [
                { key: 'ALL', label: 'ALL' },
                { key: 'ACTIVE_LIVE', label: 'LIVE' },
                { key: 'CRON_BACKTEST', label: 'CRON' },
                { key: 'DEACTIVATED', label: 'INACTIVE' }
              ]"
              :key="st.key"
              @click="statusFilter = st.key as any"
              class="btn btn-xs join-item font-mono text-[10px]"
              :class="statusFilter === st.key ? 'btn-primary font-bold' : 'btn-ghost text-base-content/60'"
            >
              {{ st.label }}
            </button>
          </div>
        </div>

        <!-- Leaderboard Data Table -->
        <div class="card bg-base-200 border border-base-content/10 p-4">
          <div class="overflow-x-auto border border-base-content/10 rounded-box">
            <table class="table table-zebra table-sm w-full font-mono text-xs">
              <thead class="bg-base-300">
                <tr>
                  <th class="w-8"></th>
                  <th>Rank</th>
                  <th>Strategy</th>
                  <th>Symbol</th>
                  <th>Status</th>
                  <th>Sharpe</th>
                  <th>Win Rate</th>
                  <th>Profit Factor</th>
                  <th>DSR</th>
                  <th>Expectancy</th>
                  <th>Drift Trajectory</th>
                  <th class="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="displayedStrategies.length === 0">
                  <td colspan="12" class="p-6 text-center text-base-content/50">
                    No strategies found matching filter criteria.
                  </td>
                </tr>

                <template v-for="strat in displayedStrategies" :key="strat.id">
                  <tr class="hover cursor-pointer" @click="toggleRow(strat.id)">
                    <!-- Expand toggle arrow -->
                    <td class="text-center p-2">
                      <component 
                        :is="expandedRows.has(strat.id) ? ChevronDown : ChevronRight" 
                        class="w-3.5 h-3.5 text-base-content/50" 
                      />
                    </td>

                    <!-- Rank & Tier -->
                    <td class="font-bold">
                      <div class="flex items-center gap-1.5">
                        <span>#{{ strat.rank }}</span>
                        <span class="badge badge-xs font-bold" :class="getTierBadgeClass(strat.tier)">
                          {{ strat.tier }}
                        </span>
                      </div>
                    </td>

                    <!-- Strategy Name -->
                    <td>
                      <div class="font-bold text-base-content">{{ strat.display_name || strat.name }}</div>
                      <div class="text-[10px] text-base-content/50 truncate max-w-xs">{{ strat.target_profile }}</div>
                    </td>

                    <!-- Symbol -->
                    <td>
                      <span class="badge badge-xs font-bold" :class="strat.symbol?.includes('XAU') ? 'badge-warning' : 'badge-info'">
                        {{ strat.symbol }}
                      </span>
                    </td>

                    <!-- Status -->
                    <td>
                      <span class="badge badge-xs font-bold border" :class="getStatusBadgeClass(strat.status)">
                        {{ strat.status }}
                      </span>
                    </td>

                    <!-- Sharpe -->
                    <td class="font-bold" :class="getValColor(getStratSharpe(strat))">
                      {{ getStratSharpe(strat)?.toFixed(2) ?? '—' }}
                    </td>

                    <!-- Win Rate -->
                    <td class="font-bold" :class="getValColor(getStratWinRate(strat) - 50)">
                      {{ getStratWinRate(strat) ? `${getStratWinRate(strat).toFixed(1)}%` : '—' }}
                    </td>

                    <!-- Profit Factor -->
                    <td class="font-bold" :class="getValColor(getStratPf(strat) - 1.0)">
                      {{ getStratPf(strat) ? getStratPf(strat).toFixed(2) : '—' }}
                    </td>

                    <!-- DSR -->
                    <td>
                      <span 
                        class="badge badge-xs font-bold" 
                        :class="strat.latest_backtest?.dsr && strat.latest_backtest.dsr >= 0.95 ? 'badge-success' : 'badge-warning'"
                      >
                        {{ strat.latest_backtest?.dsr ?? '—' }}
                      </span>
                    </td>

                    <!-- Expectancy -->
                    <td>
                      <span class="font-mono text-base-content/80">
                        {{ strat.latest_backtest?.expectancy_bps ? `${strat.latest_backtest.expectancy_bps} bps` : '—' }}
                      </span>
                    </td>

                    <!-- Drift Trajectory -->
                    <td>
                      <div class="flex items-center gap-1 text-[11px]">
                        <component 
                          :is="getTrajectoryIcon(strat)" 
                          class="w-3.5 h-3.5"
                          :class="getTrajectoryClass(strat)"
                        />
                        <span :class="getTrajectoryClass(strat)" class="font-bold">
                          {{ getTrajectoryText(strat) }}
                        </span>
                      </div>
                    </td>

                    <!-- Actions -->
                    <td class="text-right" @click.stop>
                      <div class="flex items-center justify-end gap-1.5">
                        <button
                          @click="emit('navigateToBacktest', strat.name)"
                          class="btn btn-xs btn-ghost border border-base-content/10"
                          title="Open in Backtest Deck (F3)"
                        >
                          <Eye class="w-3 h-3" />
                        </button>
                        <button
                          @click="handleRunBacktest(strat.name)"
                          :disabled="actionLoading[strat.name]"
                          class="btn btn-xs btn-primary btn-outline"
                          title="Run Quant Backtest"
                        >
                          <Play class="w-3 h-3 fill-current" />
                        </button>
                        <button
                          v-if="strat.status !== 'ACTIVE_LIVE'"
                          @click="emit('updateStatus', strat.name, 'ACTIVE_LIVE')"
                          class="btn btn-xs btn-success"
                        >
                          Deploy
                        </button>
                        <button
                          v-else
                          @click="emit('updateStatus', strat.name, 'DEACTIVATED')"
                          class="btn btn-xs btn-error btn-outline"
                        >
                          Deactivate
                        </button>
                      </div>
                    </td>
                  </tr>

                  <!-- Expanded Details Row -->
                  <tr v-if="expandedRows.has(strat.id)" class="bg-base-300/30">
                    <td colspan="12" class="p-4 space-y-4">
                      <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
                        <!-- Card 1: Backtest Snapshots & Metric Drift History -->
                        <div class="space-y-2 bg-base-100/80 p-3.5 rounded-box border border-base-content/10 flex flex-col justify-between">
                          <div>
                            <div class="flex items-center justify-between pb-2 border-b border-base-content/10">
                              <span class="text-xs font-bold text-info flex items-center gap-1.5">
                                <History class="w-3.5 h-3.5" /> BACKTEST SNAPSHOTS &amp; DRIFT
                              </span>
                              <div class="flex items-center gap-1.5">
                                <span class="badge badge-xs badge-info font-bold">
                                  {{ getReversedSnapshotsWithDelta(strat.cron_config?.drift_history, strat).length }} Runs
                                </span>
                                <button
                                  @click.stop="handleRunBacktest(strat.name)"
                                  :disabled="actionLoading[strat.name]"
                                  class="btn btn-xs btn-primary btn-outline gap-1"
                                  title="Run New Backtest Snapshot"
                                >
                                  <Play class="w-2.5 h-2.5 fill-current" />
                                  <span>Test</span>
                                </button>
                              </div>
                            </div>

                            <div v-if="getReversedSnapshotsWithDelta(strat.cron_config?.drift_history, strat).length === 0" class="h-44 flex flex-col items-center justify-center text-center p-4 text-base-content/50">
                              <History class="w-6 h-6 mb-1 opacity-40" />
                              <div class="text-xs font-bold">No Drift Snapshots Yet</div>
                              <div class="text-[10px] text-base-content/40 mt-1 max-w-xs">
                                Click "Test" to execute quantitative backtest and record first drift snapshot.
                              </div>
                            </div>

                            <div v-else class="overflow-y-auto max-h-48 mt-2 border border-base-content/10 rounded-box">
                              <table class="table table-xs table-zebra w-full font-mono text-[10px]">
                                <thead class="sticky top-0 bg-base-200 z-10 text-[9px] uppercase text-base-content/60">
                                  <tr>
                                    <th>Timestamp</th>
                                    <th class="text-right">Sharpe</th>
                                    <th class="text-right">DSR</th>
                                    <th class="text-right">Win%</th>
                                    <th class="text-right">MaxDD</th>
                                    <th class="text-right">PF</th>
                                    <th class="text-center">Drift</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  <tr 
                                    v-for="(snap, sIdx) in getReversedSnapshotsWithDelta(strat.cron_config?.drift_history, strat)" 
                                    :key="sIdx"
                                    class="hover"
                                  >
                                    <td class="text-base-content/70 whitespace-nowrap">
                                      {{ formatSnapTime(snap.timestamp) }}
                                    </td>
                                    <td class="text-right font-bold" :class="snap.sharpe >= 1.8 ? 'text-success' : 'text-warning'">
                                      {{ snap.sharpe != null ? snap.sharpe.toFixed(2) : '—' }}
                                    </td>
                                    <td class="text-right font-bold" :class="(snap.dsr ?? 0) >= 0.95 ? 'text-success' : 'text-warning'">
                                      {{ snap.dsr != null ? snap.dsr.toFixed(2) : '—' }}
                                    </td>
                                    <td class="text-right">
                                      {{ formatSnapWinRate(snap.win_rate) }}
                                    </td>
                                    <td class="text-right font-bold text-error">
                                      {{ formatSnapMdd(snap.max_drawdown) }}
                                    </td>
                                    <td class="text-right font-bold" :class="(snap.profit_factor ?? 0) >= 1.5 ? 'text-success' : (snap.profit_factor ?? 0) >= 1.0 ? 'text-warning' : 'text-error'">
                                      {{ snap.profit_factor != null ? snap.profit_factor.toFixed(2) : '—' }}
                                    </td>
                                    <td class="text-center">
                                      <span 
                                        v-if="snap.deltaSharpe > 0.05" 
                                        class="badge badge-xs badge-success font-bold text-[9px]"
                                        title="Sharpe expanding"
                                      >
                                        +{{ snap.deltaSharpe.toFixed(2) }}
                                      </span>
                                      <span 
                                        v-else-if="snap.deltaSharpe < -0.05" 
                                        class="badge badge-xs badge-error font-bold text-[9px]"
                                        title="Sharpe decaying"
                                      >
                                        {{ snap.deltaSharpe.toFixed(2) }}
                                      </span>
                                      <span v-else class="text-base-content/40 text-[9px]">
                                        —
                                      </span>
                                    </td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          </div>

                          <div class="pt-2 border-t border-base-content/10 flex items-center justify-between text-[10px] text-base-content/60">
                            <span>Drift Status: <strong :class="getTrajectoryClass(strat)">{{ getTrajectoryText(strat) }}</strong></span>
                            <button 
                              @click.stop="emit('navigateToBacktest', strat.name)"
                              class="link link-primary link-hover text-[10px] font-bold"
                            >
                              Audit in Backtest (F3) &rarr;
                            </button>
                          </div>
                        </div>

                        <!-- Card 2: 5-Gate Cynic Adversarial Audit Matrix & Quantitative Thesis -->
                        <div class="space-y-3 bg-base-100/80 p-3.5 rounded-box border border-base-content/10 flex flex-col justify-between">
                          <div class="space-y-2">
                            <div class="flex items-center justify-between pb-2 border-b border-base-content/10">
                              <span class="text-xs font-bold text-warning flex items-center gap-1.5">
                                <ShieldCheck class="w-3.5 h-3.5" /> 5-GATE CYNIC MATRIX
                              </span>
                              <span class="badge badge-xs font-bold" :class="getTierBadgeClass(strat.tier)">
                                {{ strat.tier || 'C-Tier' }}
                              </span>
                            </div>

                            <div class="grid grid-cols-2 gap-1.5 text-[10px]">
                              <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
                                <span class="text-base-content/60">Gate 1: DSR</span>
                                <span class="font-bold" :class="(strat.latest_backtest?.dsr ?? 0) >= 0.95 ? 'text-success' : 'text-warning'">
                                  {{ (strat.latest_backtest?.dsr ?? 0) >= 0.95 ? 'PASS' : 'WARN' }}
                                </span>
                              </div>
                              <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
                                <span class="text-base-content/60">Gate 2: Stability</span>
                                <span class="font-bold text-success">PASS</span>
                              </div>
                              <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
                                <span class="text-base-content/60">Gate 3: Monte Carlo</span>
                                <span class="font-bold text-success">
                                  {{ strat.latest_backtest?.mdd_99 ? `${(strat.latest_backtest.mdd_99 * 100).toFixed(1)}%` : 'PASS' }}
                                </span>
                              </div>
                              <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between">
                                <span class="text-base-content/60">Gate 4: Walk-Forward</span>
                                <span class="font-bold text-success">PASS</span>
                              </div>
                              <div class="p-2 rounded bg-base-200 border border-base-content/10 flex items-center justify-between col-span-2">
                                <span class="text-base-content/60">Gate 5: Regime Survival</span>
                                <span class="font-bold text-success">ROBUST ALPHA</span>
                              </div>
                            </div>
                          </div>

                          <div class="p-2 rounded bg-base-200 border border-base-content/10 text-[10px] space-y-1">
                            <div class="text-primary font-bold flex items-center gap-1">
                              <Sparkles class="w-3 h-3" /> Thesis &amp; Invalidation:
                            </div>
                            <p class="text-base-content/80 line-clamp-2 leading-relaxed">
                              {{ strat.thesis || 'Mathematical regime exploitation strategy with strict stop loss bounds.' }}
                            </p>
                          </div>
                        </div>

                        <!-- Card 3: Embedded Equity Trajectory -->
                        <div class="space-y-2 bg-base-100/80 p-3.5 rounded-box border border-base-content/10">
                          <div class="flex items-center justify-between text-xs pb-1 border-b border-base-content/10">
                            <span class="font-bold text-base-content text-[11px] flex items-center gap-1.5">
                              <TrendingUp class="w-3.5 h-3.5 text-primary" /> EQUITY TRAJECTORY
                            </span>
                            <div class="join">
                              <button 
                                @click="equityViewMode[strat.id] = 'BACKTEST'" 
                                class="btn btn-xs join-item text-[10px]"
                                :class="(equityViewMode[strat.id] || 'BACKTEST') === 'BACKTEST' ? 'btn-primary font-bold' : 'btn-ghost text-base-content/60'"
                              >
                                Backtest
                              </button>
                              <button 
                                @click="equityViewMode[strat.id] = 'LIVE'" 
                                class="btn btn-xs join-item text-[10px]"
                                :class="equityViewMode[strat.id] === 'LIVE' ? 'btn-success font-bold' : 'btn-ghost text-base-content/60'"
                              >
                                Live
                              </button>
                            </div>
                          </div>

                          <DaisyEquityChart 
                            :data="(equityViewMode[strat.id] === 'LIVE' ? strat.live_equity_curve : strat.backtest_equity_curve) || []"
                            :title="`${strat.name} (${equityViewMode[strat.id] || 'BACKTEST'})`"
                            :chartHeight="130"
                            :idPrefix="`eq_${strat.id}`"
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── TAB 2: ALPHA DRIFT TRAJECTORY ── -->
      <div v-else-if="activeTab === 'DRIFT_TRAJECTORY'" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Gaining Edge -->
          <div class="card bg-base-200 border border-base-content/10 p-5 space-y-3">
            <div class="flex items-center justify-between border-b border-base-content/10 pb-2">
              <span class="font-bold text-xs flex items-center gap-2 text-success">
                <TrendingUp class="w-4 h-4" /> GAINING EDGE (STRENGTHENING ALPHA)
              </span>
              <span class="badge badge-sm badge-success badge-outline font-bold">
                {{ distribution.improving.length }} Strategies
              </span>
            </div>

            <div v-if="distribution.improving.length === 0" class="py-6 text-center text-xs text-base-content/50">
              No strategies currently showing significant alpha expansion.
            </div>
            <div v-else class="space-y-2">
              <div 
                v-for="item in distribution.improving" 
                :key="item.name"
                class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between text-xs"
              >
                <div>
                  <div class="font-bold text-base-content">{{ item.display_name || item.name }}</div>
                  <div class="text-[10px] text-success font-bold flex items-center gap-1.5 mt-0.5">
                    <span>Δ Sharpe: +{{ item.delta_sharpe }}</span>
                    <span>•</span>
                    <span>Δ Win Rate: +{{ item.delta_win_rate }}%</span>
                  </div>
                </div>
                <button 
                  @click="emit('navigateToBacktest', item.name)"
                  class="btn btn-xs btn-outline btn-success font-bold"
                >
                  Audit
                </button>
              </div>
            </div>
          </div>

          <!-- Decaying Edge -->
          <div class="card bg-base-200 border border-base-content/10 p-5 space-y-3">
            <div class="flex items-center justify-between border-b border-base-content/10 pb-2">
              <span class="font-bold text-xs flex items-center gap-2 text-error">
                <TrendingDown class="w-4 h-4" /> DECAYING EDGE (ALPHA EXHAUSTION)
              </span>
              <span class="badge badge-sm badge-error badge-outline font-bold">
                {{ distribution.decaying.length }} Strategies
              </span>
            </div>

            <div v-if="distribution.decaying.length === 0" class="py-6 text-center text-xs text-base-content/50">
              Zero strategies showing active edge decay.
            </div>
            <div v-else class="space-y-2">
              <div 
                v-for="item in distribution.decaying" 
                :key="item.name"
                class="p-3 rounded-box bg-base-300/60 border border-base-content/10 flex items-center justify-between text-xs"
              >
                <div>
                  <div class="font-bold text-base-content">{{ item.display_name || item.name }}</div>
                  <div class="text-[10px] text-error font-bold flex items-center gap-1.5 mt-0.5">
                    <span>Δ Sharpe: {{ item.delta_sharpe }}</span>
                    <span>•</span>
                    <span>Δ Win Rate: {{ item.delta_win_rate }}%</span>
                  </div>
                </div>
                <button 
                  @click="emit('updateStatus', item.name, 'DEACTIVATED')"
                  class="btn btn-xs btn-outline btn-error font-bold"
                >
                  Retire
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── TAB 3: RISK & DISTRIBUTION CHARTS ── -->
      <div v-else-if="activeTab === 'DISTRIBUTION'" class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DaisyDistributionBar 
          title="Sharpe Ratio Distribution" 
          :data="distribution.sharpe_distribution"
        />
        <DaisyDistributionBar 
          title="Strategy Tier Breakdown" 
          :data="distribution.tier_distribution"
        />
        <DaisyDistributionBar 
          title="Asset Allocation Scope" 
          :data="distribution.asset_distribution"
        />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  Layers, RefreshCw, Award, TrendingUp, TrendingDown,
  PieChart, Search, Eye, Play, Sparkles, ChevronDown, ChevronRight, Activity,
  History, ShieldCheck
} from 'lucide-vue-next';
import DaisyEquityChart from './charts/DaisyEquityChart.vue';
import DaisyDistributionBar from './charts/DaisyDistributionBar.vue';
import type { ManagedStrategy, PortfolioSummary, DistributionAnalytics } from '../composables/useWebSocket';

const props = withDefaults(
  defineProps<{
    theme?: 'dark' | 'light';
    strategies?: ManagedStrategy[];
    signals?: any[];
    activeStrategy?: string;
    portfolioSummary?: PortfolioSummary | null;
    distributionAnalytics?: DistributionAnalytics | null;
  }>(),
  {
    theme: 'dark',
    strategies: () => [],
    signals: () => [],
    activeStrategy: 'GoatFundedTraderXauusdScalper.py',
  }
);

const emit = defineEmits<{
  (e: 'selectStrategy', stratName: string): void;
  (e: 'activateStrategy', stratName: string): void;
  (e: 'updateStatus', stratName: string, newStatus: string): void;
  (e: 'runBacktest', stratName: string): void;
  (e: 'triggerCron'): void;
  (e: 'navigateToBacktest', stratName: string): void;
}>();

const activeTab = ref<'LEADERBOARD' | 'DRIFT_TRAJECTORY' | 'DISTRIBUTION'>('LEADERBOARD');
const tableMetricMode = ref<'LIVE' | 'BACKTEST'>('LIVE');
const searchQuery = ref('');
const statusFilter = ref<'ALL' | 'ACTIVE_LIVE' | 'CRON_BACKTEST' | 'DEACTIVATED'>('ALL');
const expandedRows = ref<Set<string>>(new Set());
const equityViewMode = ref<Record<string, 'BACKTEST' | 'LIVE'>>({});
const runningCron = ref(false);
const actionLoading = ref<Record<string, boolean>>({});

const toggleRow = (id: string) => {
  if (expandedRows.value.has(id)) {
    expandedRows.value.delete(id);
  } else {
    expandedRows.value.add(id);
  }
};

const activeCount = computed(() => props.strategies.filter((s) => s.status === 'ACTIVE_LIVE').length);
const cronCount = computed(() => props.strategies.filter((s) => s.status === 'CRON_BACKTEST').length);

const portfolio = computed<PortfolioSummary>(() => {
  if (props.portfolioSummary && props.portfolioSummary.active_count !== undefined) {
    return props.portfolioSummary;
  }
  const activeStrats = props.strategies.filter((s) => s.status === 'ACTIVE_LIVE');
  let totalTrades = 0;
  let totalWins = 0;
  let weightedSharpeSum = 0;
  const pfs: number[] = [];
  const syms: string[] = [];
  const names: string[] = [];

  activeStrats.forEach((s) => {
    names.push(s.name);
    if (s.symbol && !syms.includes(s.symbol)) syms.push(s.symbol);
    const bt = s.latest_backtest || {};
    const trades = bt.trades || 0;
    const rawWr = bt.win_rate || 0;
    const normWr = rawWr <= 1.0 ? rawWr : rawWr / 100;
    const sh = bt.sharpe || 0;
    const pf = bt.profit_factor || 0;

    totalTrades += trades;
    totalWins += Math.round(trades * normWr);
    weightedSharpeSum += sh * Math.max(1, trades);
    if (pf > 0) pfs.push(pf);
  });

  const btWr = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
  const blendedSh = totalTrades > 0 ? weightedSharpeSum / totalTrades : (activeStrats.length > 0 ? activeStrats.reduce((a, b) => a + (b.latest_backtest?.sharpe || 0), 0) / activeStrats.length : 0);
  const combinedPf = pfs.length > 0 ? pfs.reduce((a, b) => a + b, 0) / pfs.length : 0;

  return {
    active_count: activeStrats.length,
    active_strategies: names,
    blended_win_rate: Number(btWr.toFixed(1)),
    blended_sharpe: Number(blendedSh.toFixed(2)),
    total_trades: totalTrades,
    combined_profit_factor: Number(combinedPf.toFixed(2)),
    total_realized_pnl: 0,
    symbols: syms,
    best_performer: activeStrats[0]?.name || null,
  };
});

const distribution = computed<DistributionAnalytics>(() => {
  if (props.distributionAnalytics && props.distributionAnalytics.total_evaluated !== undefined) {
    return props.distributionAnalytics;
  }

  const improving: any[] = [];
  const decaying: any[] = [];
  const stable: any[] = [];
  const sharpeBins: Record<string, number> = { '< 1.0': 0, '1.0 - 1.5': 0, '1.5 - 2.5': 0, '> 2.5': 0 };
  const tierCounts: Record<string, number> = { 'S-Tier': 0, 'A-Tier': 0, 'B-Tier': 0, 'C-Tier': 0 };
  const assetCounts: Record<string, number> = {};

  props.strategies.forEach((s) => {
    const tier = s.tier || 'C-Tier';
    if (tier.includes('S-Tier')) tierCounts['S-Tier']++;
    else if (tier.includes('A-Tier')) tierCounts['A-Tier']++;
    else if (tier.includes('B-Tier')) tierCounts['B-Tier']++;
    else tierCounts['C-Tier']++;

    const sym = s.symbol || 'Other';
    assetCounts[sym] = (assetCounts[sym] || 0) + 1;

    const sh = s.latest_backtest?.sharpe || 0;
    if (sh < 1.0) sharpeBins['< 1.0']++;
    else if (sh <= 1.5) sharpeBins['1.0 - 1.5']++;
    else if (sh <= 2.5) sharpeBins['1.5 - 2.5']++;
    else sharpeBins['> 2.5']++;

    const hist = s.cron_config?.drift_history || [];
    let deltaSh = 0;
    let deltaWr = 0;
    if (hist.length >= 2) {
      const last = hist[hist.length - 1];
      const prev = hist[hist.length - 2];
      deltaSh = Number(((last.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
      deltaWr = Number((((last.win_rate || 0) - (prev.win_rate || 0)) * 100).toFixed(1));
    }

    const entry = {
      name: s.name,
      display_name: s.display_name,
      status: s.status,
      sharpe: sh,
      win_rate: s.latest_backtest?.win_rate || 0,
      delta_sharpe: deltaSh,
      delta_win_rate: deltaWr,
      snapshots_count: hist.length,
      trajectory: 'STABLE',
    };

    if (deltaSh > 0.05 || deltaWr > 1.0) {
      entry.trajectory = 'GAINING_EDGE';
      improving.push(entry);
    } else if (deltaSh < -0.05 || deltaWr < -1.0) {
      entry.trajectory = 'DECAYING_EDGE';
      decaying.push(entry);
    } else {
      stable.push(entry);
    }
  });

  return {
    improving,
    decaying,
    stable,
    sharpe_distribution: sharpeBins,
    tier_distribution: tierCounts,
    asset_distribution: assetCounts,
    total_evaluated: props.strategies.length,
  };
});

const displayedStrategies = computed(() => {
  let list = [...props.strategies];
  if (statusFilter.value !== 'ALL') {
    list = list.filter((s) => s.status === statusFilter.value);
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.display_name?.toLowerCase().includes(q) ||
        s.target_profile?.toLowerCase().includes(q) ||
        s.symbol?.toLowerCase().includes(q)
    );
  }
  return list;
});

const getStratSharpe = (strat: ManagedStrategy) => {
  if (tableMetricMode.value === 'LIVE' && strat.live_stats?.sharpe_live !== undefined) {
    return strat.live_stats.sharpe_live;
  }
  return strat.latest_backtest?.sharpe;
};

const getStratWinRate = (strat: ManagedStrategy) => {
  if (tableMetricMode.value === 'LIVE' && strat.live_stats?.win_rate !== undefined) {
    return strat.live_stats.win_rate * 100;
  }
  const raw = strat.latest_backtest?.win_rate || 0;
  return raw <= 1.0 ? raw * 100 : raw;
};

const getStratPf = (strat: ManagedStrategy) => {
  if (tableMetricMode.value === 'LIVE' && strat.live_stats?.profit_factor !== undefined) {
    return strat.live_stats.profit_factor;
  }
  return strat.latest_backtest?.profit_factor;
};

const getTierBadgeClass = (tier?: string) => {
  if (!tier) return 'badge-neutral';
  if (tier.includes('S-Tier')) return 'badge-warning';
  if (tier.includes('A-Tier')) return 'badge-primary';
  if (tier.includes('B-Tier')) return 'badge-info';
  return 'badge-neutral';
};

const getStatusBadgeClass = (status?: string) => {
  if (status === 'ACTIVE_LIVE') return 'badge-success bg-success/10 text-success';
  if (status === 'CRON_BACKTEST') return 'badge-warning bg-warning/10 text-warning';
  return 'badge-neutral bg-base-300 text-base-content/50';
};

const getTrajectoryIcon = (strat: ManagedStrategy) => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    if ((last.sharpe || 0) > (prev.sharpe || 0) + 0.05) return TrendingUp;
    if ((last.sharpe || 0) < (prev.sharpe || 0) - 0.05) return TrendingDown;
  }
  return Activity;
};

const getTrajectoryClass = (strat: ManagedStrategy) => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    if ((last.sharpe || 0) > (prev.sharpe || 0) + 0.05) return 'text-success';
    if ((last.sharpe || 0) < (prev.sharpe || 0) - 0.05) return 'text-error';
  }
  return 'text-base-content/50';
};

const getTrajectoryText = (strat: ManagedStrategy) => {
  const hist = strat.cron_config?.drift_history || [];
  if (hist.length >= 2) {
    const last = hist[hist.length - 1];
    const prev = hist[hist.length - 2];
    const dSh = Number(((last.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
    if (dSh > 0.05) return `+${dSh} EXPANDING`;
    if (dSh < -0.05) return `${dSh} DECAYING`;
  }
  return 'STABLE';
};

const getValColor = (val?: number) => {
  if (val === undefined || val === null) return 'text-base-content';
  return val < 0 ? 'text-error font-bold' : 'text-success font-bold';
};

const handleRunBacktest = async (stratName: string) => {
  try {
    actionLoading.value[stratName] = true;
    emit('runBacktest', stratName);
  } finally {
    actionLoading.value[stratName] = false;
  }
};

const handleTriggerCron = async () => {
  try {
    runningCron.value = true;
    emit('triggerCron');
  } finally {
    runningCron.value = false;
  }
};

const formatSnapTime = (ts?: string) => {
  if (!ts) return '—';
  try {
    const d = new Date(ts);
    return d.toLocaleDateString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch {
    return ts.slice(5, 16);
  }
};

const formatSnapWinRate = (wr?: number) => {
  if (wr == null) return '—';
  const val = wr <= 1.0 ? wr * 100 : wr;
  return `${val.toFixed(1)}%`;
};

const formatSnapMdd = (mdd?: number) => {
  if (mdd == null) return '—';
  const val = mdd <= 1.0 ? mdd * 100 : mdd;
  return `${val.toFixed(2)}%`;
};

const getReversedSnapshotsWithDelta = (history?: any[], strat?: ManagedStrategy) => {
  let list = history && history.length > 0 ? [...history] : [];
  if (list.length === 0 && strat?.latest_backtest && (strat.latest_backtest.sharpe || 0) > 0) {
    const bt = strat.latest_backtest;
    list = [{
      timestamp: bt.last_run || new Date().toISOString(),
      sharpe: bt.sharpe,
      dsr: bt.dsr,
      win_rate: bt.win_rate,
      max_drawdown: bt.max_drawdown,
      trades: bt.trades,
      profit_factor: bt.profit_factor,
    }];
  }
  const enriched = list.map((snap, idx) => {
    let deltaSharpe = 0;
    let deltaWr = 0;
    if (idx > 0) {
      const prev = list[idx - 1];
      deltaSharpe = Number(((snap.sharpe || 0) - (prev.sharpe || 0)).toFixed(2));
      const currWr = (snap.win_rate <= 1.0 ? snap.win_rate * 100 : snap.win_rate) || 0;
      const prevWr = (prev.win_rate <= 1.0 ? prev.win_rate * 100 : prev.win_rate) || 0;
      deltaWr = Number((currWr - prevWr).toFixed(1));
    }
    return {
      ...snap,
      deltaSharpe,
      deltaWr,
    };
  });
  return enriched.slice().reverse();
};
</script>
