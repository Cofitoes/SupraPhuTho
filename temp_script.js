
        window.onerror = function (message, source, lineno, colno, error) {
            var errDiv = document.getElementById('demo-error-overlay');
            if (!errDiv) {
                errDiv = document.createElement('div');
                errDiv.id = 'demo-error-overlay';
                errDiv.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);color:red;z-index:999999;padding:20px;font-family:monospace;white-space:pre-wrap;overflow:auto;';
                document.body.appendChild(errDiv);
            }
            errDiv.innerText += "\nError: " + message + "\nSource: " + source + "\nLine: " + lineno + "\nCol: " + colno + "\n" + (error ? error.stack : "") + "\n-------------------\n";
            console.error("Error: " + message + "\nLine: " + lineno + "\nCol: " + colno + "\n" + (error ? error.stack : ""));
            return false;
        };
        window.onunhandledrejection = function (event) {
            var errDiv = document.getElementById('demo-error-overlay');
            if (!errDiv) {
                errDiv = document.createElement('div');
                errDiv.id = 'demo-error-overlay';
                errDiv.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);color:red;z-index:999999;padding:20px;font-family:monospace;white-space:pre-wrap;overflow:auto;';
                document.body.appendChild(errDiv);
            }
            errDiv.innerText += "\nUnhandled Promise Rejection: " + event.reason + "\n-------------------\n";
            console.error(event.reason);
        };
        window.addEventListener('error', function (e) {
            if (e.target && (e.target.tagName === 'SCRIPT' || e.target.tagName === 'LINK')) {
                var errDiv = document.getElementById('demo-error-overlay');
                if (!errDiv) {
                    errDiv = document.createElement('div');
                    errDiv.id = 'demo-error-overlay';
                    errDiv.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);color:orange;z-index:999999;padding:20px;font-family:monospace;white-space:pre-wrap;overflow:auto;';
                    document.body.appendChild(errDiv);
                }
                errDiv.innerText += "\nResource Load Error: Failed to load " + e.target.tagName + " from: " + (e.target.src || e.target.href) + "\n-------------------\n";
            }
        }, true);
    