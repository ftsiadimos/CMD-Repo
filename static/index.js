// =============================================================================
// INDEX PAGE JAVASCRIPT - COMMAND REPOSITORY INTERFACE
// =============================================================================
// File: static/index.js
// Purpose: Handles all client-side interactivity for the main commands listing page
// Dependencies: Bootstrap 5 (for CSS classes), Modern browser with clipboard API support
// Features:
//   - Copy command text to system clipboard with visual feedback
//   - Expandable/collapsible table rows for detailed command viewing
//   - Expand/collapse all rows functionality via header arrow
//   - Responsive design with mobile-friendly interactions
// =============================================================================

/**
 * Main DOM Content Loaded Event Handler
 * Ensures all DOM elements are available before attaching event listeners
 * This prevents JavaScript errors when scripts load before HTML elements
 */
document.addEventListener('DOMContentLoaded', function () {
    // =============================================================================
    // COPY TO CLIPBOARD FUNCTIONALITY
    // =============================================================================
    // Provides cross-browser clipboard copying with fallback for older browsers
    // Uses modern Clipboard API when available, falls back to document.execCommand
    // Returns a Promise for consistent error handling

    /**
     * Copies text to the system clipboard using the most appropriate method
     * @param {string} text - The text content to copy to clipboard
     * @returns {Promise} Resolves on successful copy, rejects on failure
     */
    function copyText(text) {
        // Input validation - reject empty or invalid text
        if (!text) return Promise.reject(new Error('No text to copy'));

        // Modern Clipboard API (preferred method for security and reliability)
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }

        // Fallback for older browsers using traditional method
        // Create a temporary textarea element for selection and copying
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');  // Prevent user editing during copy
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';  // Position off-screen to avoid visual flicker
        document.body.appendChild(ta);

        // Select the text and attempt to copy
        ta.select();
        try {
            var ok = document.execCommand('copy');
            document.body.removeChild(ta);  // Clean up temporary element
            return ok ? Promise.resolve() : Promise.reject(new Error('copy failed'));
        } catch (e) {
            document.body.removeChild(ta);  // Clean up on error
            return Promise.reject(e);
        }
    }

    // =============================================================================
    // TYPING EFFECT FUNCTIONALITY
    // =============================================================================
    // Creates a realistic terminal typing effect for command display
    // Types out text character by character with configurable speed

    /**
     * Types out text character by character with a blinking cursor effect
     * @param {HTMLElement} element - The element to type into
     * @param {string} text - The text to type
     * @param {number} speed - Milliseconds between each character (default: 50)
     */
    function typeCommand(element, text, speed = 50) {
        let index = 0;
        element.textContent = '';
        element.classList.add('typing');
        element.classList.remove('typed');
        
        function type() {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
                setTimeout(type, speed);
            } else {
                // Typing complete - remove cursor after a brief pause
                setTimeout(() => {
                    element.classList.remove('typing');
                    element.classList.add('typed');
                }, 500);
            }
        }
        
        // Small delay before starting to type
        setTimeout(type, 100);
    }

    // =============================================================================
    // ROW EXPANSION/COLLAPSE FUNCTIONALITY
    // =============================================================================
    // Allows users to expand table rows to see full command details
    // Clicking on the arrow cell toggles the expanded state
    // Visual cues (pointer cursor, hover effects) indicate clickable areas
    // Prevents expansion when clicking on other cells or interactive elements

    /**
     * Attaches click event listeners to all table rows for expansion/collapse
     * Only allows expansion when clicking on the arrow cell
     * Excludes clicks on copy buttons and forms to prevent conflicts
     * Includes smooth animations for better user experience
     */
    document.querySelectorAll('tbody tr').forEach(function (row) {
        row.addEventListener('click', function (e) {
            // Prevent row expansion when clicking on interactive elements
            // This allows buttons and forms to work normally
            if (e.target.closest('.copy-btn') || e.target.closest('form')) return;

            // Only allow expansion when clicking on the arrow cell
            // Check if the clicked element contains the expand arrow
            const clickedCell = e.target.closest('td');
            if (!clickedCell) return; // Not clicked on a cell
            
            const isArrowCell = clickedCell.querySelector('.expand-arrow') !== null;
            
            // Only expand if clicked on arrow cell
            if (!isArrowCell) return;

            // Get the description cell for colspan manipulation
            const descCell = row.querySelector('.desc-cell');
            const isExpanding = !row.classList.contains('expanded');

            // Toggle the 'expanded' CSS class to show/hide additional content
            row.classList.toggle('expanded');

            // Dynamically adjust table cell spanning for expanded layout
            // When expanded, the description cell should span multiple columns
            const cmdCell = row.querySelector('.cmd-cell');
            const subCell = row.querySelector('.col-subcmds');
            const cmdText = cmdCell.querySelector('.truncate-2').textContent; 
            
            if (row.classList.contains('expanded')) {
                // Hide the original command and subcommand cells
                cmdCell.style.display = 'none';
                if (subCell) subCell.style.display = 'none';
                
                // Expand description cell to span 7 columns (full width including command and subcommands columns)
                descCell.setAttribute('colspan', '7');
                
                // Create command header above description if it doesn't exist
                let commandHeader = descCell.querySelector('.command-header');
                if (!commandHeader) {
                    commandHeader = document.createElement('div');
                    commandHeader.className = 'command-header';

                    // Create command text span (typing effect will populate it)
                    const commandSpan = document.createElement('span');
                    commandSpan.className = 'command-text typing';
                    commandHeader.appendChild(commandSpan);

                    // Create copy button for the main command in expanded header
                    const copyBtn = document.createElement('button');
                    copyBtn.type = 'button';
                    copyBtn.className = 'btn btn-sm btn-outline-success ms-2 copy-expanded-btn';
                    copyBtn.title = 'Copy command';
                    copyBtn.setAttribute('aria-label', 'Copy command');
                    copyBtn.dataset.command = cmdText;
                    copyBtn.innerHTML = '<i class="bi bi-clipboard" aria-hidden="true"></i>';
                    // Prevent clicks from bubbling to row (avoid re-triggering expand)
                    copyBtn.addEventListener('click', function(ev){ ev.stopPropagation(); });

                    commandHeader.appendChild(copyBtn);
                    descCell.insertBefore(commandHeader, descCell.firstChild);

                    // Typing effect - type out command character by character
                    typeCommand(commandSpan, cmdText, 30); // 30ms per character

                    // Attach copy handler directly so dynamically created button works
                    copyBtn.addEventListener('click', function (ev) {
                        ev.stopPropagation();
                        const icon = copyBtn.querySelector('i');
                        const text = copyBtn.dataset.command || '';
                        copyText(text).then(function () {
                            icon.className = 'bi bi-check-lg';
                            copyBtn.classList.remove('btn-outline-success');
                            copyBtn.classList.add('btn-success');
                            setTimeout(function () {
                                icon.className = 'bi bi-clipboard';
                                copyBtn.classList.remove('btn-success');
                                copyBtn.classList.add('btn-outline-success');
                            }, 1500);
                        }).catch(function () {
                            icon.className = 'bi bi-x-lg';
                            copyBtn.classList.remove('btn-outline-success');
                            copyBtn.classList.add('btn-danger');
                            setTimeout(function () {
                                icon.className = 'bi bi-clipboard';
                                copyBtn.classList.remove('btn-danger');
                                copyBtn.classList.add('btn-outline-success');
                            }, 1500);
                        });
                    });
                }
                
                // Add subtle animation for expansion
                descCell.style.transition = 'all 0.3s ease';
                setTimeout(() => {
                    descCell.style.opacity = '1';
                }, 50);
            } else {
                // Show the original command and subcommand cells
                cmdCell.style.display = '';
                if (subCell) subCell.style.display = ''; 
                
                // Remove command header
                const commandHeader = descCell.querySelector('.command-header');
                if (commandHeader) {
                    commandHeader.remove();
                }
                
                // Reset to normal single-column span
                descCell.removeAttribute('colspan');
                descCell.style.opacity = '0.8';
                setTimeout(() => {
                    descCell.style.transition = '';
                    descCell.style.opacity = '';
                }, 300);
            }
        });
    });

    // =============================================================================
    // COPY BUTTON EVENT HANDLERS
    // =============================================================================
    // Handles the copy-to-clipboard buttons with visual feedback
    // Shows success/error states with appropriate icons and colors
    // Uses data attributes to store the command text to copy

    /**
     * Attaches event listeners to all copy buttons in the table
     * Provides visual feedback during copy operations
     */
    document.querySelectorAll('.copy-btn').forEach(function (btn) {
        btn.addEventListener('click', function (ev) {
            // Prevent event bubbling to avoid triggering row expansion
            ev.stopPropagation();

            // Extract command text from data attribute
            var text = btn.dataset.command || '';

            // Get reference to the button's icon for visual feedback
            var icon = btn.querySelector('i');

            // Attempt to copy text and handle the result
            copyText(text).then(function () {
                // SUCCESS STATE: Show checkmark icon and green styling
                icon.className = 'bi bi-check-lg';  // Bootstrap check icon
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-success');

                // Reset to original state after 1.5 seconds
                setTimeout(function() {
                    icon.className = 'bi bi-clipboard';  // Original clipboard icon
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-outline-primary');
                }, 1500);
            }).catch(function () {
                // ERROR STATE: Show X icon and red styling
                icon.className = 'bi bi-x-lg';  // Bootstrap X icon
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-danger');

                // Reset to original state after 1.5 seconds
                setTimeout(function() {
                    icon.className = 'bi bi-clipboard';  // Original clipboard icon
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-outline-primary');
                }, 1500);
            });
        });
    });

    // Additional copy handlers for expanded header and subcommand buttons
    document.querySelectorAll('.copy-sub-btn').forEach(function (btn) {
        btn.addEventListener('click', function (ev) {
            ev.stopPropagation();
            var text = btn.dataset.command || '';
            var icon = btn.querySelector('i');

            copyText(text).then(function () {
                icon.className = 'bi bi-check-lg';
                btn.classList.remove('btn-outline-success');
                btn.classList.add('btn-success');
                setTimeout(function () {
                    icon.className = 'bi bi-clipboard';
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-outline-success');
                }, 1500);
            }).catch(function () {
                icon.className = 'bi bi-x-lg';
                btn.classList.remove('btn-outline-success');
                btn.classList.add('btn-danger');
                setTimeout(function () {
                    icon.className = 'bi bi-clipboard';
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-outline-success');
                }, 1500);
            });
        });
    });

    // =============================================================================
    // EXPAND/COLLAPSE ALL ROWS FUNCTIONALITY
    // =============================================================================
    // Allows users to expand or collapse all table rows at once
    // Clicking the header arrow toggles all rows between expanded and collapsed states

    /**
     * Handles the expand/collapse all functionality
     * Toggles all rows and updates the header arrow visual state
     */
    const expandAllArrow = document.querySelector('.expand-all-arrow');
    if (expandAllArrow) {
        expandAllArrow.addEventListener('click', function () {
            const allRows = document.querySelectorAll('tbody tr');
            const isCurrentlyExpanded = this.classList.contains('expanded');
            
            // Toggle the header arrow visual state
            this.classList.toggle('expanded');
            
            // Update tooltip text based on new state
            if (this.classList.contains('expanded')) {
                this.setAttribute('title', 'Collapse All Rows ▲');
            } else {
                this.setAttribute('title', 'Expand All Rows ▼');
            }
            
            // Expand or collapse all rows
            allRows.forEach(function (row) {
                const descCell = row.querySelector('.desc-cell');
                const cmdCell = row.querySelector('.cmd-cell');
                const isRowExpanded = row.classList.contains('expanded');
                
                if (isCurrentlyExpanded) {
                    // Collapse all rows
                    if (isRowExpanded) {
                        row.classList.remove('expanded');
                        
                        // Show the original command and subcommand cells
                        cmdCell.style.display = '';
                        const subCell = row.querySelector('.col-subcmds');
                        if (subCell) subCell.style.display = ''; 
                        
                        // Remove command header
                        const commandHeader = descCell.querySelector('.command-header');
                        if (commandHeader) {
                            commandHeader.remove();
                        }
                        
                        descCell.removeAttribute('colspan');
                        descCell.style.opacity = '0.8';
                        setTimeout(() => {
                            descCell.style.transition = '';
                            descCell.style.opacity = '';
                        }, 300);
                    }
                } else {
                    // Expand all rows
                    if (!isRowExpanded) {
                        row.classList.add('expanded');
                        
                        // Hide the original command and subcommand cells
                        cmdCell.style.display = 'none';
                        const subCell = row.querySelector('.col-subcmds');
                        if (subCell) subCell.style.display = 'none';
                        
                        // Create command header above description
                        const cmdText = cmdCell.querySelector('.truncate-2').textContent;
                        let commandHeader = descCell.querySelector('.command-header');
                        if (!commandHeader) {
                            commandHeader = document.createElement('div');
                            commandHeader.className = 'command-header';

                            const commandSpan = document.createElement('span');
                            commandSpan.className = 'command-text';
                            commandSpan.textContent = cmdText;
                            commandHeader.appendChild(commandSpan);

                            // copy button for expanded header (no typing here)
                            const copyBtn = document.createElement('button');
                            copyBtn.type = 'button';
                            copyBtn.className = 'btn btn-sm btn-outline-success ms-2 copy-expanded-btn';
                            copyBtn.title = 'Copy command';
                            copyBtn.dataset.command = cmdText;
                            copyBtn.innerHTML = '<i class="bi bi-clipboard" aria-hidden="true"></i>';
                            copyBtn.addEventListener('click', function(ev){ ev.stopPropagation(); });
                            commandHeader.appendChild(copyBtn);

                            descCell.insertBefore(commandHeader, descCell.firstChild);

                            // attach handler
                            copyBtn.addEventListener('click', function (ev) {
                                ev.stopPropagation();
                                const icon = copyBtn.querySelector('i');
                                const text = copyBtn.dataset.command || '';
                                copyText(text).then(function () {
                                    icon.className = 'bi bi-check-lg';
                                    copyBtn.classList.remove('btn-outline-success');
                                    copyBtn.classList.add('btn-success');
                                    setTimeout(function () {
                                        icon.className = 'bi bi-clipboard';
                                        copyBtn.classList.remove('btn-success');
                                        copyBtn.classList.add('btn-outline-success');
                                    }, 1500);
                                }).catch(function () {
                                    icon.className = 'bi bi-x-lg';
                                    copyBtn.classList.remove('btn-outline-success');
                                    copyBtn.classList.add('btn-danger');
                                    setTimeout(function () {
                                        icon.className = 'bi bi-clipboard';
                                        copyBtn.classList.remove('btn-danger');
                                        copyBtn.classList.add('btn-outline-success');
                                    }, 1500);
                                });
                            });
                        }
                        
                        descCell.setAttribute('colspan', '7');
                        descCell.style.transition = 'all 0.3s ease';
                        setTimeout(() => {
                            descCell.style.opacity = '1';
                        }, 50);
                    }
                }
            });
        });
    }
});