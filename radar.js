// Tech Radar Implementation
class TechRadar {
    constructor() {
        this.width = 800;
        this.height = 800;
        this.center = { x: 400, y: 400 };
        this.radius = 350;
        this.svg = document.getElementById('radar');
        this.currentFilter = 'all';
        this.searchTerm = '';

        // Zoom and pan
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.hasMoved = false;

        this.quadrants = [
            { name: 'Techniques', angle: 0 },
            { name: 'Tools', angle: 90 },
            { name: 'Platforms', angle: 180 },
            { name: 'Languages & Frameworks', angle: 270 }
        ];

        this.rings = [
            { name: 'Adopt', radius: 0.25, color: '#10b981' },
            { name: 'Trial', radius: 0.5, color: '#06b6d4' },
            { name: 'Assess', radius: 0.75, color: '#f59e0b' },
            { name: 'Hold', radius: 1.0, color: '#ef4444' }
        ];

        this.tooltip = this.createTooltip();
        this.positionCache = {}; // Cache for blip positions
        this.loadTheme();
        this.loadData();
        this.setupEventListeners();
    }

    createTooltip() {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        document.body.appendChild(tooltip);
        return tooltip;
    }

    loadTheme() {
        const theme = localStorage.getItem('tech-radar-theme') || 'light';
        if (theme === 'light') {
            document.body.classList.add('light-theme');
        }
    }

    toggleTheme() {
        document.body.classList.toggle('light-theme');
        const theme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        localStorage.setItem('tech-radar-theme', theme);
    }

    exportSVG() {
        const svgData = this.svg.outerHTML;
        const blob = new Blob([svgData], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'tech-radar.svg';
        link.click();
        URL.revokeObjectURL(url);
    }

    resetZoom() {
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.updateTransform();
    }

    getDataSource() {
        const aiToggle = document.getElementById('ai-toggle');
        return aiToggle && aiToggle.checked ? 'data.ai.json' : 'data.json';
    }

    loadData(dataSource = null) {
        const source = dataSource || this.getDataSource();
        fetch(source)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Add unique IDs to each item for reliable tracking
                this.data = data.map((item, index) => ({ ...item, _id: index }));
                this.render();
            })
            .catch(error => {
                console.error('Error loading data:', error);
                // Show error message to user
                const container = document.querySelector('.main-content');
                if (container) {
                    container.innerHTML = `
                        <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                            <h2 style="color: var(--accent-danger); margin-bottom: 20px;">⚠️ Failed to Load Data</h2>
                            <p style="color: var(--text-secondary); margin-bottom: 20px;">
                                The radar data could not be loaded. This usually happens when opening the file directly.
                            </p>
                            <div style="background: var(--bg-card); padding: 20px; border-radius: 12px; max-width: 600px; margin: 0 auto; text-align: left;">
                                <h3 style="color: var(--text-primary); margin-bottom: 15px;">Solution:</h3>
                                <p style="color: var(--text-secondary); margin-bottom: 10px;">Run a local server:</p>
                                <pre style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; overflow-x: auto;">
<code style="color: var(--accent-secondary);">python3 -m http.server 8000</code>
                                </pre>
                                <p style="color: var(--text-secondary); margin-top: 10px;">Then open: <code style="color: var(--accent-primary);">http://localhost:8000</code></p>
                            </div>
                            <p style="color: var(--text-secondary); margin-top: 20px; font-size: 0.9rem;">
                                Error: ${error.message} (${source})
                            </p>
                        </div>
                    `;
                }
                this.data = [];
            });
    }

    setupEventListeners() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.quadrant;
                this.render();
            });
        });

        // Search
        document.getElementById('search').addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.render();
        });

        // Zoom with mouse wheel - DISABLED (fixed size radar)
        // this.svg.addEventListener('wheel', (e) => {
        //     e.preventDefault();
        //     const delta = e.deltaY > 0 ? 0.9 : 1.1;
        //     this.scale = Math.max(0.5, Math.min(3, this.scale * delta));
        //     this.updateTransform();
        // });

        // Pan with drag
        this.svg.addEventListener('mousedown', (e) => {
            // Only allow dragging on background elements, not on blips
            const isBlip = e.target.closest('.blip');

            // Don't start drag if clicking on a blip
            if (!isBlip) {
                const isBackground = e.target === this.svg ||
                                     e.target.tagName === 'svg' ||
                                     (e.target.tagName === 'circle' && e.target.getAttribute('stroke-dasharray')) ||
                                     (e.target.tagName === 'line') ||
                                     (e.target.tagName === 'text' && e.target.classList.contains('quadrant-label'));

                if (isBackground) {
                    this.isDragging = true;
                    this.dragStart = { x: e.clientX - this.translateX, y: e.clientY - this.translateY };
                    this.svg.style.cursor = 'grabbing';
                }
            }
        });

        this.svg.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                e.preventDefault();
                const newX = e.clientX - this.dragStart.x;
                const newY = e.clientY - this.dragStart.y;

                // Only update if moved more than 2 pixels (deadzone to prevent jitter)
                if (Math.abs(newX - this.translateX) > 2 || Math.abs(newY - this.translateY) > 2) {
                    this.translateX = newX;
                    this.translateY = newY;
                    this.hasMoved = true;
                    this.updateTransform();
                }
            }
        });

        this.svg.addEventListener('mouseup', (e) => {
            // If we were dragging and didn't move much, don't prevent click events
            if (this.isDragging && !this.hasMoved) {
                // Reset immediately so click events can fire
            }
            this.isDragging = false;
            this.hasMoved = false;
            this.svg.style.cursor = 'default';
        });

        this.svg.addEventListener('mouseleave', () => {
            this.isDragging = false;
            this.hasMoved = false;
            this.svg.style.cursor = 'default';
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ignore if typing in search box
            if (e.target.tagName === 'INPUT') return;

            // Reset zoom with 'r' or '0' - DISABLED (fixed size radar)
            // if (e.key === 'r' || e.key === 'R' || e.key === '0') {
            //     this.resetZoom();
            // }
            // Zoom in with '+' - DISABLED (fixed size radar)
            // if (e.key === '+' || e.key === '=') {
            //     this.scale = Math.min(3, this.scale * 1.1);
            //     this.updateTransform();
            // }
            // Zoom out with '-' - DISABLED (fixed size radar)
            // if (e.key === '-' || e.key === '_') {
            //     this.scale = Math.max(0.5, this.scale * 0.9);
            //     this.updateTransform();
            // }
            // Toggle theme with 't'
            if (e.key === 't' || e.key === 'T') {
                this.toggleTheme();
            }
            // Export with 'e'
            if (e.key === 'e' || e.key === 'E') {
                this.exportSVG();
            }
        });

        // Theme toggle button
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // AI toggle
        document.getElementById('ai-toggle').addEventListener('change', () => {
            this.loadData();
        });
    }

    updateTransform() {
        const mainGroup = this.svg.querySelector('g.main-group');
        if (mainGroup) {
            mainGroup.setAttribute('transform',
                `translate(${this.translateX} ${this.translateY}) scale(${this.scale})`);
        }
    }

    render() {
        this.svg.innerHTML = '';
        this.drawRadar();
        this.drawBlips();
        this.renderTechList();
    }

    drawRadar() {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'main-group');
        g.setAttribute('transform', `translate(${this.translateX} ${this.translateY}) scale(${this.scale})`);

        // Draw rings with gradients
        this.rings.forEach((ring, i) => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', this.center.x);
            circle.setAttribute('cy', this.center.y);
            circle.setAttribute('r', ring.radius * this.radius);
            circle.setAttribute('fill', 'none');
            circle.setAttribute('stroke', ring.color);
            circle.setAttribute('stroke-width', '2');
            circle.setAttribute('stroke-opacity', '0.3');
            circle.setAttribute('stroke-dasharray', '5,5');

            // Add animation
            const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            animate.setAttribute('attributeName', 'stroke-dashoffset');
            animate.setAttribute('from', '0');
            animate.setAttribute('to', '10');
            animate.setAttribute('dur', '2s');
            animate.setAttribute('repeatCount', 'indefinite');
            circle.appendChild(animate);

            g.appendChild(circle);

            // Ring labels with better styling
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', this.center.x);
            text.setAttribute('y', this.center.y - (ring.radius * this.radius) + 20);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', ring.color);
            text.setAttribute('font-size', '14');
            text.setAttribute('font-weight', 'bold');
            text.setAttribute('opacity', '0.8');
            text.textContent = ring.name.toUpperCase();
            g.appendChild(text);
        });

        // Draw quadrant lines
        for (let i = 0; i < 4; i++) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            const angle = (i * 90) * Math.PI / 180;
            line.setAttribute('x1', this.center.x);
            line.setAttribute('y1', this.center.y);
            line.setAttribute('x2', this.center.x + Math.cos(angle) * this.radius);
            line.setAttribute('y2', this.center.y + Math.sin(angle) * this.radius);
            line.setAttribute('stroke', '#a1a1aa');
            line.setAttribute('stroke-width', '1.5');
            line.setAttribute('stroke-opacity', '0.4');
            g.appendChild(line);
        }

        // Draw quadrant labels
        this.quadrants.forEach((quadrant, i) => {
            const angle = (quadrant.angle + 45) * Math.PI / 180;
            const labelRadius = this.radius * 0.85;
            const x = this.center.x + Math.cos(angle) * labelRadius;
            const y = this.center.y + Math.sin(angle) * labelRadius;

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', y);
            text.setAttribute('class', 'quadrant-label');
            text.textContent = quadrant.name;
            g.appendChild(text);
        });

        this.svg.appendChild(g);
    }

    drawBlips() {
        const filteredData = this.getFilteredData();
        const mainGroup = this.svg.querySelector('.main-group');

        filteredData.forEach((item, filteredIndex) => {
            const position = this.calculatePosition(item);

            // Use the unique _id we assigned when loading data
            const originalIndex = item._id;

            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', 'blip');
            g.setAttribute('data-id', originalIndex);

            // Removed pulse effect to prevent jitter - only show on hover
            // Draw blip outer ring (will only be visible on hover)
            const outerCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            outerCircle.setAttribute('cx', position.x);
            outerCircle.setAttribute('cy', position.y);
            outerCircle.setAttribute('r', '14');
            outerCircle.setAttribute('fill', 'none');
            outerCircle.setAttribute('stroke', this.rings[item.ring].color);
            outerCircle.setAttribute('stroke-width', '1');
            outerCircle.setAttribute('opacity', '0');
            outerCircle.setAttribute('class', 'blip-outer-ring');

            g.appendChild(outerCircle);

            // Draw blip circle
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', position.x);
            circle.setAttribute('cy', position.y);
            circle.setAttribute('r', '10');
            circle.setAttribute('fill', this.rings[item.ring].color);
            circle.setAttribute('stroke', '#e4e4e7');
            circle.setAttribute('stroke-width', '2');
            g.appendChild(circle);

            // Draw number label
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', position.x);
            text.setAttribute('y', position.y + 4);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', '11');
            text.setAttribute('font-weight', 'bold');
            text.textContent = originalIndex + 1;
            g.appendChild(text);

            g.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent click from bubbling to SVG
                this.showTechDetails(item);
            });
            g.addEventListener('mouseenter', (e) => {
                this.highlightTech(originalIndex);
                this.showTooltip(item, e);
            });
            g.addEventListener('mouseleave', () => {
                this.unhighlightTech(originalIndex);
                this.hideTooltip();
            });
            g.addEventListener('mousemove', (e) => this.updateTooltipPosition(e));

            mainGroup.appendChild(g);
        });
    }

    showTooltip(item, e) {
        this.tooltip.textContent = item.name;
        this.tooltip.classList.add('show');
        this.updateTooltipPosition(e);
    }

    hideTooltip() {
        this.tooltip.classList.remove('show');
    }

    updateTooltipPosition(e) {
        this.tooltip.style.left = `${e.clientX + 15}px`;
        this.tooltip.style.top = `${e.clientY + 15}px`;
    }

    calculatePosition(item) {
        // Create a unique key for this item
        const cacheKey = `${item.name}-${item.quadrant}-${item.ring}`;

        // Return cached position if it exists
        if (this.positionCache[cacheKey]) {
            return this.positionCache[cacheKey];
        }

        const ring = this.rings[item.ring];
        const quadrant = this.quadrants[item.quadrant];

        // Use item name as seed for consistent randomization
        const seed = this.hashCode(item.name);
        const random1 = this.seededRandom(seed);
        const random2 = this.seededRandom(seed + 1);

        // Random position within the quadrant and ring
        const minRadius = item.ring === 0 ? 0 : this.rings[item.ring - 1].radius * this.radius;
        const maxRadius = ring.radius * this.radius;
        const radius = minRadius + (maxRadius - minRadius) * (0.3 + random1 * 0.5);

        const angleStart = quadrant.angle;
        const angle = (angleStart + 10 + random2 * 70) * Math.PI / 180;

        const position = {
            x: this.center.x + Math.cos(angle) * radius,
            y: this.center.y + Math.sin(angle) * radius
        };

        // Cache the position
        this.positionCache[cacheKey] = position;

        return position;
    }

    // Simple hash function for seeding
    hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash);
    }

    // Seeded random number generator
    seededRandom(seed) {
        const x = Math.sin(seed) * 10000;
        return x - Math.floor(x);
    }

    getFilteredData() {
        if (!this.data) return [];

        return this.data.filter(item => {
            const matchesFilter = this.currentFilter === 'all' ||
                                  item.quadrant === parseInt(this.currentFilter);
            const matchesSearch = !this.searchTerm ||
                                  item.name.toLowerCase().includes(this.searchTerm) ||
                                  item.description.toLowerCase().includes(this.searchTerm);
            return matchesFilter && matchesSearch;
        });
    }

    showTechDetails(item) {
        const detailsDiv = document.getElementById('tech-details');
        detailsDiv.style.display = 'block';

        document.getElementById('tech-name').textContent = item.name;
        document.getElementById('tech-ring').textContent = this.rings[item.ring].name;
        document.getElementById('tech-quadrant').textContent = this.quadrants[item.quadrant].name;
        document.getElementById('tech-description').textContent = item.description;
    }

    highlightTech(id) {
        // Find blip by data-id attribute, not by array index
        const blip = document.querySelector(`.blip[data-id="${id}"]`);
        if (blip) {
            blip.classList.add('highlighted');
        }

        // Find tech item by data-original-index attribute, not by array index
        const techItem = document.querySelector(`.tech-item[data-original-index="${id}"]`);
        if (techItem) {
            techItem.classList.add('highlighted');
            techItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    unhighlightTech(id) {
        // Find blip by data-id attribute, not by array index
        const blip = document.querySelector(`.blip[data-id="${id}"]`);
        if (blip) {
            blip.classList.remove('highlighted');
        }

        // Find tech item by data-original-index attribute, not by array index
        const techItem = document.querySelector(`.tech-item[data-original-index="${id}"]`);
        if (techItem) {
            techItem.classList.remove('highlighted');
        }
    }

    renderTechList() {
        const listDiv = document.getElementById('tech-list');
        const filteredData = this.getFilteredData();

        if (filteredData.length === 0) {
            listDiv.innerHTML = '<p style="color: #999;">No technologies found</p>';
            return;
        }

        // Group by ring
        const groupedByRing = {};
        filteredData.forEach((item) => {
            // Use the unique _id we assigned when loading data
            const originalIndex = item._id;
            const ringName = this.rings[item.ring].name;
            if (!groupedByRing[ringName]) {
                groupedByRing[ringName] = [];
            }
            groupedByRing[ringName].push({ ...item, originalIndex });
        });

        let html = '<h3>Technologies</h3>';

        this.rings.forEach(ring => {
            const items = groupedByRing[ring.name];
            if (items && items.length > 0) {
                html += `<div class="tech-category">
                    <h4>${ring.name}</h4>`;

                items.forEach(item => {
                    html += `<div class="tech-item" data-original-index="${item.originalIndex}">
                        <span class="tech-number" style="background: ${ring.color}">${item.originalIndex + 1}</span>
                        <span>${item.name}</span>
                    </div>`;
                });

                html += '</div>';
            }
        });

        listDiv.innerHTML = html;

        // Add click handlers
        document.querySelectorAll('.tech-item').forEach(itemEl => {
            const originalIndex = parseInt(itemEl.dataset.originalIndex);
            const item = this.data[originalIndex];

            itemEl.addEventListener('click', () => {
                this.showTechDetails(item);
                this.highlightTech(originalIndex);
            });
            itemEl.addEventListener('mouseenter', () => this.highlightTech(originalIndex));
            itemEl.addEventListener('mouseleave', () => this.unhighlightTech(originalIndex));
        });
    }
}

// Initialize radar when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TechRadar();
});
