function colorCode(value) {
    const val = value.toLowerCase();
    if (val === 'high') return `<span style="color: red; font-weight: bold;">${value}</span>`;
    if (val === 'medium') return `<span style="color: orange; font-weight: bold;">${value}</span>`;
    if (val === 'low') return `<span style="color: green; font-weight: bold;">${value}</span>`;
    return value.charAt(0).toUpperCase() + value.slice(1);
}

function highlightRiskTitle(text) {
    return text.replace(/^(.*?Risk.*?)(\s*-\s*)(.*?)(:.*)/i,
                        '<strong>$1</strong>$2<strong>$3</strong>$4');
}

export function formatOutputWithHighlights(output, type) {
    if (type === "output1") {
        return output.map(([index, description]) => {
            const formatted = `<strong>Risk ${index}:</strong> ${description}`;
            return highlightRiskTitle(formatted);
        }).join("<br><br>");
    }

    else if (type === "output2") {
        return output.map((a, i) => {
            let impactHTML = "N/A";
            try {
                impactHTML = a.impact.split(', ').map(pair => {
                    const [k, v] = pair.split(': ');
                    return `&nbsp;&nbsp;&nbsp;&nbsp;- <strong>${k}:</strong> ${colorCode(v)}`;
                }).join('<br>') + '<br>';
            } catch (e) {
                console.debug(a);
            }

            const content = `
                <strong>Detailed Analysis</strong> for ${a.description}<br>
                <strong>Likelihood:</strong> ${colorCode(a.likelihood)}<br>
                <strong>Impact:</strong><br>${impactHTML}<br>
                <strong>Root causes:</strong> ${a.triggering_root_cause_events}<br>
                <strong>Intermediate events:</strong> ${a.triggering_intermediate_events}<br>
                <strong>Consequences:</strong> ${a.consequences}<br>
                ${a.interdependencies ? `<strong>Interdependencies:</strong> ${a.interdependencies}<br>` : ""}
            `;
            return highlightRiskTitle(content.trim());
        }).join("<br><br>");
    }

    else if (type === "output3") {
        return output.map(kris => {
            const header = highlightRiskTitle(`<strong>KRIs:</strong>`);
            const kriItems = kris.kris.map((kri, idx) => 
                `&nbsp;&nbsp;&nbsp;&nbsp;<strong>${idx + 1}. ${kri.indicator}</strong>: ${kri.rationale}`
            ).join("<br>");
            return `${header}<br>${kriItems}<br>`;
        }).join("<br>");
    }

    else if (type === "output4") {
        return output.map(controls => {
            const header = highlightRiskTitle(`<strong>Internal Controls:</strong>`);
            const controlItems = controls.controls.map((control, idx) => 
                `&nbsp;&nbsp;&nbsp;&nbsp;<strong>${idx + 1}. ${control.control}</strong>: ${control.explanation}`
            ).join("<br>");
            return `${header}<br>${controlItems}<br>`;
        }).join("<br>");
    }

    else if (type === "output5") {
        const a = output;
        let impactHTML = "N/A";
        try {
            impactHTML = a.impact.split(', ').map(pair => {
                const [k, v] = pair.split(': ');
                return `&nbsp;&nbsp;&nbsp;&nbsp;- <strong>${k}:</strong> ${colorCode(v)}`;
            }).join('<br>') + '<br>';
        } catch (e) {
            console.debug(a);
        }

        const content = `
            <strong>Initial Analysis</strong> for ${a.description}<br>
            <strong>Likelihood:</strong> ${colorCode(a.likelihood)}<br>
            <strong>Impact:</strong><br>${impactHTML}<br>
            <strong>Root causes:</strong> ${a.triggering_root_cause_events}<br>
            <strong>Intermediate events:</strong> ${a.triggering_intermediate_events}<br>
            <strong>Consequences:</strong> ${a.consequences}<br>
            ${a.interdependencies ? `<strong>Interdependencies:</strong> ${a.interdependencies}<br>` : ""}
        `;

        return highlightRiskTitle(content.trim());
    }

    return "Unsupported output type.";
}
