<html>
    <head>
<!--        <style type="text/css">
            ${css}
        </style>
-->    </head>
    <body>
        %for o in objects :
        <table width = '100%' style="font-size: 12px;border-bottom:1pt solid black;">
            <tr >
                <td style="vertical-align: top;max-height: 45px;">
                    ${helper.embed_image('jpeg',str(o.company_id.logo),180, 85)}
                </td>
                <td>
                    <div>${o.company_id.name or ''|entity}</div>
                    <br>${o.company_id.partner_id.street or ''|entity} No. 
                                                ${o.company_id.partner_id.street2 or ''|entity}
                                                ${o.company_id.partner_id.zip or ''|entity}
                                                <br/>${o.company_id.partner_id.city or ''|entity}
                                                , ${o.company_id.partner_id.state_id.name or ''|entity}
                                                , ${o.company_id.partner_id.country_id.name or ''|entity}
                </td>
<!--                <td>
                    <div>${_("Printing Date:")} ${time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </td>
-->            </tr>
        </table>                                   

        <table width=100% style="font-size: 10px;font-weight: bold;">
            <tr>
                <td width='50%' style="padding-top: 10px;">${_("Journal Entries: ")} ${o.name or '' |entity}</td>
                <td width='50%' style="padding-top: 10px;">${_("Date: ")} ${o.date or '' |entity}</td>
            </tr>
            <tr>
                <td style="padding-bottom: 10px;">${_("Reference: ")} ${o.ref or '' |entity}</td>
                <td style="padding-bottom: 10px;">${_("Period: ")} ${o.period_id.name or '' |entity}</td>
            </tr>
        </table>
        <table width=100% style="font-size: 9px;">
            <tr style="text-align: center;">
                <td width='20%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Account")}</div>
                </td>
                <td width='15%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Name")}</div>
                </td>
                <td width='15%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Partner")}</div>
                </td>
                <td width='5%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Invoice")}</div>
                </td>
                <td width='10%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Debit")}</div>
                </td>
                <td width='10%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Credit")}</div>
                </td>
                <td width='12%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Analytic Account")}</div>
                </td>
                <td width='7%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Amount Currency")}</div>
                </td>
                <td width='6%' style="font-weight: bold;border-bottom:1pt solid black;border-top:1pt solid black;">
                    <div>${_("Currency")}</div>
                </td>
            %for line in o.line_id:
            <tr>
                <td style="border-bottom:1pt solid gray;">
                    <div>${line.account_id.code or '' |entity} - ${line.account_id.name or '' |entity}</div>
                </td>
                <td style="word-wrap: break-word;border-bottom:1pt solid gray;">
                    <div>${line.name or '' |entity}</div>
                </td>
                <td style="border-bottom:1pt solid gray;">
                    <div>${line.partner_id.name or ''}</div>
                </td>
                <td style="border-bottom:1pt solid gray;">
                    <div>${line.invoice.supplier_invoice_number or line.invoice.number or '' |entity}</div>
                </td>
                <td style="text-align:right;border-bottom:1pt solid gray;">
                    <div>${formatLang(line.debit or 0.0) |entity}</div>
                </td>
                <td style="text-align:right;border-bottom:1pt solid gray;">
                    <div>${formatLang(line.credit or 0.0) |entity}</div>
                </td>
                <td style="border-bottom:1pt solid gray;">
                    <div>${line.analytic_account_id.name or '' |entity}</div>
                </td>
                <td style="text-align:right;border-bottom:1pt solid gray;">
                    <div>${formatLang(line.amount_currency or 0.0) |entity}</div>
                </td>
                <td style="border-bottom:1pt solid gray;">
                    <div>${line.currency_id.name or '' |entity}</div>
                </td>
            </tr>
            %endfor
            <tr>
                <td colspan="4" style="text-align:right;font-weight: bold;padding-top: 10px;">SUMAS: </td>
                <td style="text-align:right;font-weight: bold;padding-top: 10px;">
                    <div width='6%' >${formatLang(get_total_debit_credit(o.line_id)['sum_tot_debit'] or 0.0) |entity}</div>
                </td>
                <td style="text-align:right;font-weight: bold;padding-top: 10px;">
                    <div width='6%'>${formatLang(get_total_debit_credit(o.line_id)['sum_tot_credit'] or 0.0) |entity}</div>
                </td>
                <td colspan="3"></td>
            </tr>
            
        </table>
        %if len(loop._iterable) != 1 and loop.index != len(loop._iterable)-1:
            <p style="page-break-after:always"></p>
        %endif
    %endfor
    </body>
</html>
