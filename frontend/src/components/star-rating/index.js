import styles from "./style.module.css";

const StarRating = ({
  rating,
  ratingsCount = 0,
  userRating,
  onRate,
  isSaving = false,
}) => {
  const roundedRating = rating === null || rating === undefined
    ? 0
    : Math.round(rating);
  const selectedRating = userRating || roundedRating;
  const ratingText = ratingsCount
    ? `${Number(rating).toFixed(1)} из 5 на основе ${ratingsCount} оценок`
    : "Пока нет оценок";

  return (
    <div className={styles.rating} aria-label={ratingText}>
      <div className={styles.stars} aria-hidden={!onRate}>
        {[1, 2, 3, 4, 5].map((value) => {
          const isFilled = value <= selectedRating;

          if (!onRate) {
            return (
              <span
                className={isFilled ? styles.starActive : styles.star}
                key={value}
              >
                ★
              </span>
            );
          }

          return (
            <button
              aria-label={`Поставить ${value} из 5`}
              className={isFilled ? styles.buttonActive : styles.button}
              disabled={isSaving}
              key={value}
              onClick={() => onRate(value)}
              type="button"
            >
              ★
            </button>
          );
        })}
      </div>
      <span className={styles.value}>
        {ratingsCount ? `${Number(rating).toFixed(1)} (${ratingsCount})` : "Нет оценок"}
      </span>
    </div>
  );
};

export default StarRating;
