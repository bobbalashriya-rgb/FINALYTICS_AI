export const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'Data unavailable';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact' }).format(value);
};

export const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'Data unavailable';
    return new Intl.NumberFormat('en-US', { style: 'percent', minimumFractionDigits: 2 }).format(value);
};

export const formatNumber = (value) => {
    if (value === null || value === undefined) return 'Data unavailable';
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
};

