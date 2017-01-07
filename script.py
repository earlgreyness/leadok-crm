import arrow


import leadok.costs
import leadok.leads


if __name__ == '__main__':

    for dow in [1, 2, 3, 4, 5, 6, 7]:
        today = arrow.now()
        a_year_ago = arrow.now().replace(months=-6)

        date_start = a_year_ago
        date_finish = today

        costs = leadok.costs.get_costs(a_year_ago.date(), today.date())

        cost = 0
        leads = 0

        for begin, end in arrow.Arrow.span_range('day', date_start, date_finish):
            if begin.isoweekday() == dow:
                try:
                    cost += sum(costs[begin.date()][name] for name in costs[begin.date()])
                except KeyError:
                    continue
                leads += leadok.leads.count_leads(
                    datetime_span=(begin, end),
                    exclude_bracks=True,
                    exclude_test=True,
                )

        print('DOW: {}, \nLeads: {}, \nExpenses: {}, \nLead Price: {}\n\n\n'.format(dow, leads, cost, cost / leads))



