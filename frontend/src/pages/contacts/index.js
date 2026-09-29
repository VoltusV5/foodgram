import MetaTags from "react-meta-tags";
import { Container, Main, Title } from "../../components";
import styles from "./styles.module.css";

const CONTACT_EMAIL = "maxt.spb@gmail.com";

const Contacts = () => (
  <Main>
    <Container>
      <MetaTags>
        <title>Контакты</title>
        <meta name="description" content="Контакты администрации Фудграм" />
      </MetaTags>
      <section className={styles.contacts}>
        <Title title="Контакты" />
        <p className={styles.text}>
          Если у вас есть вопрос, предложение или сообщение об ошибке,
          напишите администрации Фудграм:
        </p>
        <a className={styles.email} href={`mailto:${CONTACT_EMAIL}`}>
          {CONTACT_EMAIL}
        </a>
      </section>
    </Container>
  </Main>
);

export default Contacts;
