function ChipButton({ label, selected, onClick }) {
    return (
        <button
            type="button"
            className={selected ? "chip selected" : "chip"}
            onClick={onClick}
        >
            {label}
        </button>
    );
}

export default ChipButton;